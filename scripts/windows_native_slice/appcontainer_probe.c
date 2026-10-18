/* Project-owned, non-admitting Windows canary. No CAD or routing work.
 * Build twice with PROBE_ROLE=1/2 to observe different executable images.
 * The controller supplies independently reachable IPv4 endpoints. Only an
 * explicit WSAEACCES is a network-denial observation; other errors are unknown.
 */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0A00
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <sddl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <errno.h>

#ifndef PROBE_ROLE
#error PROBE_ROLE must be 1 or 2
#endif

typedef struct {
    DWORD is_container;
    DWORD capabilities;
    char sid[256];
} TOKEN_FACTS;

static int token_facts(HANDLE process, TOKEN_FACTS *facts) {
    HANDLE token = NULL;
    DWORD used = 0;
    BYTE groups[8192], package[8192];
    LPSTR sid = NULL;
    int ok = 0;
    ZeroMemory(facts, sizeof(*facts));
    if (!OpenProcessToken(process, TOKEN_QUERY, &token)) goto done;
    if (!GetTokenInformation(token, TokenIsAppContainer, &facts->is_container,
                             sizeof(facts->is_container), &used)) goto done;
    if (!GetTokenInformation(token, TokenCapabilities, groups, sizeof(groups), &used)) goto done;
    facts->capabilities = ((TOKEN_GROUPS *)groups)->GroupCount;
    if (!GetTokenInformation(token, TokenAppContainerSid, package, sizeof(package), &used)) goto done;
    if (((TOKEN_APPCONTAINER_INFORMATION *)package)->TokenAppContainer != NULL) {
        if (!ConvertSidToStringSidA(((TOKEN_APPCONTAINER_INFORMATION *)package)->TokenAppContainer, &sid)) goto done;
        if (strcpy_s(facts->sid, sizeof(facts->sid), sid) != 0) goto done;
    }
    ok = 1;
done:
    if (sid) LocalFree(sid);
    if (token) CloseHandle(token);
    return ok;
}

static void emit_token(const char *kind, DWORD pid, const TOKEN_FACTS *facts) {
    printf("{\"kind\":\"%s\",\"pid\":%lu,\"role\":%d,\"is_appcontainer\":%lu,"
           "\"capabilities\":%lu,\"sid\":\"%s\"}\n", kind,
           (unsigned long)pid, PROBE_ROLE, (unsigned long)facts->is_container,
           (unsigned long)facts->capabilities, facts->sid);
    fflush(stdout);
}

static int tcp_probe(const char *address, unsigned short port, const char *label) {
    SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    int error = 0, connected = 0;
    if (sock == INVALID_SOCKET) {
        error = WSAGetLastError();
    } else {
        struct sockaddr_in target;
        u_long nonblocking = 1;
        ZeroMemory(&target, sizeof(target));
        target.sin_family = AF_INET;
        target.sin_port = htons(port);
        if (InetPtonA(AF_INET, address, &target.sin_addr) != 1 ||
            ioctlsocket(sock, FIONBIO, &nonblocking) != 0) {
            error = WSAGetLastError();
            if (error == 0) error = WSAEINVAL;
        } else if (connect(sock, (struct sockaddr *)&target, sizeof(target)) == 0) {
            connected = 1;
        } else {
            error = WSAGetLastError();
            if (error == WSAEWOULDBLOCK) {
                fd_set writable, errors;
                struct timeval wait = {2, 0};
                int ready, length = sizeof(error);
                FD_ZERO(&writable); FD_ZERO(&errors);
                FD_SET(sock, &writable); FD_SET(sock, &errors);
                ready = select(0, NULL, &writable, &errors, &wait);
                if (ready > 0) {
                    if (getsockopt(sock, SOL_SOCKET, SO_ERROR, (char *)&error, &length) != 0)
                        error = WSAGetLastError();
                    connected = error == 0;
                } else error = ready == SOCKET_ERROR ? WSAGetLastError() : WSAETIMEDOUT;
            }
        }
        closesocket(sock);
    }
    printf("{\"kind\":\"tcp\",\"role\":%d,\"pid\":%lu,\"endpoint\":\"%s\","
           "\"connected\":%s,\"wsa_error\":%d,\"explicit_access_denied\":%s}\n",
           PROBE_ROLE, (unsigned long)GetCurrentProcessId(), label,
           connected ? "true" : "false", error,
           !connected && error == WSAEACCES ? "true" : "false");
    fflush(stdout);
    return !connected && error == WSAEACCES;
}

int wmain(int argc, wchar_t **argv) {
    TOKEN_FACTS self, child;
    WSADATA winsock;
    STARTUPINFOW startup;
    PROCESS_INFORMATION process = {0};
    wchar_t command[32768], *end = NULL;
    char address[16];
    unsigned long port, hold;
    DWORD child_exit = 0;
    int created = 0, failed = 1;
    volatile int role = PROBE_ROLE;
    if (argc != 5) return 64;
    errno = 0; port = wcstoul(argv[2], &end, 10);
    if (errno || !*argv[2] || *end || port == 0 || port > 65535) return 64;
    errno = 0; hold = wcstoul(argv[4], &end, 10);
    if (errno || !*argv[4] || *end || hold > 15) return 64;
    if (!WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, argv[1], -1,
                             address, sizeof(address), NULL, NULL)) return 64;
    if (!token_facts(GetCurrentProcess(), &self)) return 65;
    emit_token("self_token", GetCurrentProcessId(), &self);
    if (self.is_container != 1 || self.capabilities != 0 || self.sid[0] == 0) return 66;
    if (WSAStartup(MAKEWORD(2, 2), &winsock) != 0) return 67;
    if (!tcp_probe("127.0.0.1", (unsigned short)port, "owned_loopback") ||
        !tcp_probe(address, 443, "public_ipv4")) goto done;
    if (role == 1) {
        if (wcschr(argv[3], L'"') || wcscmp(argv[3], L"-") == 0) goto done;
        if (swprintf_s(command, 32768, L"\"%ls\" %ls %lu - %lu", argv[3], argv[1], port, hold) < 0) goto done;
        ZeroMemory(&startup, sizeof(startup)); startup.cb = sizeof(startup);
        startup.dwFlags = STARTF_USESTDHANDLES;
        startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
        startup.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
        startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
        ZeroMemory(&process, sizeof(process));
        if (!CreateProcessW(argv[3], command, NULL, NULL, TRUE, CREATE_SUSPENDED | CREATE_NO_WINDOW,
                            NULL, NULL, &startup, &process)) {
            printf("{\"kind\":\"child_launch_error\",\"winerror\":%lu}\n", (unsigned long)GetLastError());
            fflush(stdout); goto done;
        }
        created = 1;
        if (!token_facts(process.hProcess, &child)) goto done;
        emit_token("suspended_child_token", process.dwProcessId, &child);
        if (child.is_container != self.is_container || child.capabilities != 0 || strcmp(child.sid, self.sid) != 0) goto done;
        if (ResumeThread(process.hThread) == (DWORD)-1) goto done;
        printf("{\"kind\":\"child_resumed\",\"pid\":%lu}\n", (unsigned long)process.dwProcessId);
        fflush(stdout);
        if (WaitForSingleObject(process.hProcess, 20000) != WAIT_OBJECT_0 ||
            !GetExitCodeProcess(process.hProcess, &child_exit) || child_exit != 0) goto done;
    } else if (role != 2 || wcscmp(argv[3], L"-") != 0) goto done;
    if (hold) Sleep(hold * 1000);
    failed = 0;
done:
    if (created) {
        if (WaitForSingleObject(process.hProcess, 0) != WAIT_OBJECT_0) {
            TerminateProcess(process.hProcess, 69);
            WaitForSingleObject(process.hProcess, 5000);
        }
        CloseHandle(process.hThread); CloseHandle(process.hProcess);
    }
    WSACleanup();
    return failed ? 68 : 0;
}
