/* Windows011 CI-only prototype. Not built, executed, or a Native admission gate.
 * The trusted controller journals the actual fresh-profile SID and this owner's
 * intent BEFORE PG_Arm. No receipt, PID or serialized value grants cleanup.
 */
#define _WIN32_WINNT 0x0602
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <objbase.h>
#include <initguid.h>
#include <fwpmu.h>
#include <stddef.h>
#include <string.h>
#include <wchar.h>

#define PG_API __declspec(dllexport) DWORD WINAPI
#define PG_ABI 1u
#define PG_MAGIC 0x50475349444f574eULL
#define PG_JOBS 2u
#define PG_PROCESSES 4u
#define PG_NEW 1u
#define PG_ARMED 2u
#define PG_SEALED 3u
#define PG_REMOVED 4u
#define PG_ORPHAN 5u
#define PG_ACCESS (FWPM_ACTRL_READ | FWPM_ACTRL_ADD_LINK | READ_CONTROL | DELETE)

typedef struct PG_OWNER PG_OWNER;
typedef struct PG_INFO {
    DWORD abi, bytes, state, poisoned;
    GUID sublayer;
    GUID filters[4];
    DWORD sid_bytes;
    BYTE sid[SECURITY_MAX_SID_SIZE];
    DWORD jobs, processes, policy_may_exist, last_error, abort_error;
    DWORD pending_create, pending_job;
} PG_INFO;
typedef char PG_INFO_must_be_196_bytes[(sizeof(PG_INFO) == 196) ? 1 : -1];

struct PG_OWNER {
    ULONGLONG magic;
    DWORD pid, tid, state, poisoned, last_error, abort_error;
    DWORD sid_bytes, jobs, processes, policy_may_exist;
    DWORD pending_create, pending_job;
    BYTE sid[SECURITY_MAX_SID_SIZE];
    BYTE system_sid[SECURITY_MAX_SID_SIZE];
    BYTE admins_sid[SECURITY_MAX_SID_SIZE];
    BYTE owner_sid[SECURITY_MAX_SID_SIZE];
    BYTE owner_rights_sid[SECURITY_MAX_SID_SIZE];
    DWORD acl_storage[80];
    SECURITY_DESCRIPTOR security;
    GUID sublayer, filters[4];
    HANDLE engine;
    HANDLE job[PG_JOBS];
    HANDLE process[PG_PROCESSES];
    DWORD process_job[PG_PROCESSES];
    DWORD resume_checked[PG_PROCESSES];
};

static const GUID *const pg_layers[4] = {
    &FWPM_LAYER_ALE_AUTH_CONNECT_V4, &FWPM_LAYER_ALE_AUTH_CONNECT_V6,
    &FWPM_LAYER_ALE_AUTH_RECV_ACCEPT_V4, &FWPM_LAYER_ALE_AUTH_RECV_ACCEPT_V6
};

static BOOL pg_guid_equal(const GUID *a, const GUID *b) {
    return memcmp(a, b, sizeof(*a)) == 0;
}
static DWORD pg_valid(PG_OWNER *g) {
    if (g == NULL || g->magic != PG_MAGIC || g->pid != GetCurrentProcessId() ||
        g->tid != GetCurrentThreadId()) return ERROR_INVALID_HANDLE;
    return ERROR_SUCCESS;
}
static DWORD pg_fail(PG_OWNER *g, DWORD error) {
    if (error == ERROR_SUCCESS) error = ERROR_INVALID_DATA;
    g->poisoned = 1; g->last_error = error; g->state = PG_ORPHAN;
    return error;
}
static DWORD pg_last(void) {
    DWORD e = GetLastError();
    return e == ERROR_SUCCESS ? ERROR_INVALID_DATA : e;
}
static BOOL pg_ci(void) {
    WCHAR value[128];
    DWORD n = GetEnvironmentVariableW(L"GITHUB_ACTIONS", value, 128);
    if (n != 4 || wcscmp(value, L"true") != 0) return FALSE;
    n = GetEnvironmentVariableW(L"RUNNER_OS", value, 128);
    if (n != 7 || wcscmp(value, L"Windows") != 0) return FALSE;
    n = GetEnvironmentVariableW(L"RUNNER_ENVIRONMENT", value, 128);
    if (n != 13 || wcscmp(value, L"github-hosted") != 0) return FALSE;
    n = GetEnvironmentVariableW(L"GITHUB_REPOSITORY", value, 128);
    return n == 25 && wcscmp(value, L"faisalm7/KiCad-Autorouter") == 0;
}
static DWORD pg_security(PG_OWNER *g) {
    DWORD n = SECURITY_MAX_SID_SIZE;
    DWORD needed = 0, error = ERROR_SUCCESS;
    HANDLE token = NULL;
    union { ULONGLONG alignment; BYTE bytes[1024]; } owner_buffer;
    PSID owner;
    PACL acl = (PACL)g->acl_storage;
    if (!CreateWellKnownSid(WinLocalSystemSid, NULL, g->system_sid, &n)) return pg_last();
    n = SECURITY_MAX_SID_SIZE;
    if (!CreateWellKnownSid(WinBuiltinAdministratorsSid, NULL, g->admins_sid, &n)) return pg_last();
    n = SECURITY_MAX_SID_SIZE;
    if (!CreateWellKnownSid(WinCreatorOwnerRightsSid, NULL, g->owner_rights_sid, &n)) return pg_last();
    /* Request only the actual assignable default owner. Never enable a
     * privilege or substitute an arbitrary user/package owner on rejection. */
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &token)) return pg_last();
    ZeroMemory(&owner_buffer, sizeof(owner_buffer));
    if (!GetTokenInformation(token, TokenOwner, owner_buffer.bytes, (DWORD)sizeof(owner_buffer.bytes), &needed)) {
        error = pg_last();
    } else {
        owner = ((TOKEN_OWNER *)owner_buffer.bytes)->Owner;
        if (needed < sizeof(TOKEN_OWNER) || owner == NULL || !IsValidSid(owner) ||
            GetLengthSid(owner) > SECURITY_MAX_SID_SIZE ||
            (!EqualSid(owner, g->system_sid) && !EqualSid(owner, g->admins_sid))) error = ERROR_INVALID_OWNER;
        else if (!CopySid(SECURITY_MAX_SID_SIZE, g->owner_sid, owner)) error = pg_last();
    }
    if (!CloseHandle(token) && error == ERROR_SUCCESS) error = pg_last();
    if (error != ERROR_SUCCESS) return error;
    if (!InitializeAcl(acl, (DWORD)sizeof(g->acl_storage), ACL_REVISION) ||
        !AddAccessDeniedAceEx(acl, ACL_REVISION, 0, WRITE_DAC | WRITE_OWNER, g->owner_rights_sid) ||
        !AddAccessAllowedAceEx(acl, ACL_REVISION, 0, PG_ACCESS, g->system_sid) ||
        !AddAccessAllowedAceEx(acl, ACL_REVISION, 0, PG_ACCESS, g->admins_sid) ||
        !InitializeSecurityDescriptor(&g->security, SECURITY_DESCRIPTOR_REVISION) ||
        !SetSecurityDescriptorOwner(&g->security, g->owner_sid, FALSE) ||
        !SetSecurityDescriptorGroup(&g->security, g->admins_sid, FALSE) ||
        !SetSecurityDescriptorDacl(&g->security, TRUE, acl, FALSE) ||
        !SetSecurityDescriptorControl(&g->security, SE_DACL_PROTECTED, SE_DACL_PROTECTED)) return pg_last();
    return ERROR_SUCCESS;
}
static DWORD pg_check_security(PG_OWNER *g, const GUID *key, BOOL filter) {
    PACL acl = NULL;
    PSID owner = NULL, group = NULL;
    PSECURITY_DESCRIPTOR sd = NULL;
    SECURITY_DESCRIPTOR_CONTROL control = 0;
    DWORD revision = 0, seen = 0, i, error;
    error = filter ? FwpmFilterGetSecurityInfoByKey0(g->engine, key,
        DACL_SECURITY_INFORMATION | OWNER_SECURITY_INFORMATION | GROUP_SECURITY_INFORMATION,
        &owner, &group, &acl, NULL, &sd) :
        FwpmSubLayerGetSecurityInfoByKey0(g->engine, key,
        DACL_SECURITY_INFORMATION | OWNER_SECURITY_INFORMATION | GROUP_SECURITY_INFORMATION,
        &owner, &group, &acl, NULL, &sd);
    if (error != ERROR_SUCCESS) return error;
    if (sd == NULL || acl == NULL || owner == NULL || group == NULL ||
        !IsValidSid(owner) || !EqualSid(owner, g->owner_sid) ||
        !IsValidSid(group) || !EqualSid(group, g->admins_sid) ||
        !IsValidSecurityDescriptor(sd) || !IsValidAcl(acl) ||
        !GetSecurityDescriptorControl(sd, &control, &revision) ||
        (control & SE_DACL_PROTECTED) == 0 || acl->AceCount != 3) error = ERROR_INVALID_SECURITY_DESCR;
    for (i = 0; error == ERROR_SUCCESS && i < 3; ++i) {
        ACCESS_ALLOWED_ACE *ace = NULL;
        PSID sid;
        DWORD bit, expected;
        if (!GetAce(acl, i, (LPVOID *)&ace)) { error = pg_last(); break; }
        sid = (PSID)&ace->SidStart;
        if (ace->Header.AceSize < offsetof(ACCESS_ALLOWED_ACE, SidStart) + 8 ||
            ace->Header.AceType != (i == 0 ? ACCESS_DENIED_ACE_TYPE : ACCESS_ALLOWED_ACE_TYPE) || ace->Header.AceFlags != 0 ||
            ace->Mask != (DWORD)(i == 0 ? (WRITE_DAC | WRITE_OWNER) : PG_ACCESS) ||
            8u + 4u * (*GetSidSubAuthorityCount(sid)) >
                (DWORD)ace->Header.AceSize - (DWORD)offsetof(ACCESS_ALLOWED_ACE, SidStart) ||
            !IsValidSid(sid)) { error = ERROR_INVALID_ACL; break; }
        expected = (DWORD)offsetof(ACCESS_ALLOWED_ACE, SidStart) + GetLengthSid(sid);
        if (ace->Header.AceSize != expected) { error = ERROR_INVALID_ACL; break; }
        bit = i == 0 ? (EqualSid(sid, g->owner_rights_sid) ? 4u : 0u) :
            EqualSid(sid, g->system_sid) ? 1u : EqualSid(sid, g->admins_sid) ? 2u : 0u;
        if (bit == 0 || (seen & bit) != 0) { error = ERROR_INVALID_ACL; break; }
        seen |= bit;
    }
    if (error == ERROR_SUCCESS && seen != 7) error = ERROR_INVALID_ACL;
    FwpmFreeMemory0(&sd);
    return error;
}
static DWORD pg_check_policy(PG_OWNER *g) {
    FWPM_SUBLAYER0 *sub = NULL;
    DWORD error = FwpmSubLayerGetByKey0(g->engine, &g->sublayer, &sub), i;
    if (error != ERROR_SUCCESS) return error;
    if (sub == NULL || !pg_guid_equal(&sub->subLayerKey, &g->sublayer) ||
        sub->flags != FWPM_SUBLAYER_FLAG_PERSISTENT || sub->providerKey != NULL ||
        sub->providerData.size != 0 || sub->weight != 0x7f00) error = ERROR_INVALID_DATA;
    FwpmFreeMemory0((void **)&sub);
    if (error == ERROR_SUCCESS) error = pg_check_security(g, &g->sublayer, FALSE);
    for (i = 0; error == ERROR_SUCCESS && i < 4; ++i) {
        FWPM_FILTER0 *f = NULL;
        error = FwpmFilterGetByKey0(g->engine, &g->filters[i], &f);
        if (error != ERROR_SUCCESS) break;
        if (f == NULL || !pg_guid_equal(&f->filterKey, &g->filters[i]) ||
            !pg_guid_equal(&f->layerKey, pg_layers[i]) || !pg_guid_equal(&f->subLayerKey, &g->sublayer) ||
            f->flags != FWPM_FILTER_FLAG_PERSISTENT || f->providerKey != NULL || f->providerData.size != 0 ||
            f->weight.type != FWP_UINT8 || f->weight.uint8 != 15 || f->numFilterConditions != 1 ||
            f->filterCondition == NULL || f->action.type != FWP_ACTION_BLOCK || f->rawContext != 0 || f->reserved != NULL) {
            error = ERROR_INVALID_DATA;
        } else {
            FWPM_FILTER_CONDITION0 *c = f->filterCondition;
            if (!pg_guid_equal(&c->fieldKey, &FWPM_CONDITION_ALE_PACKAGE_ID) || c->matchType != FWP_MATCH_EQUAL ||
                c->conditionValue.type != FWP_SID || c->conditionValue.sid == NULL ||
                !IsValidSid(c->conditionValue.sid) || GetLengthSid(c->conditionValue.sid) != g->sid_bytes ||
                !EqualSid(c->conditionValue.sid, g->sid)) error = ERROR_INVALID_SID;
        }
        FwpmFreeMemory0((void **)&f);
        if (error == ERROR_SUCCESS) error = pg_check_security(g, &g->filters[i], TRUE);
    }
    return error;
}
static DWORD pg_empty(PG_OWNER *g) {
    DWORD i;
    if (g->jobs == 0 || g->pending_create) return ERROR_INVALID_STATE;
    for (i = 0; i < g->jobs; ++i) {
        JOBOBJECT_BASIC_ACCOUNTING_INFORMATION a;
        ZeroMemory(&a, sizeof(a));
        if (!QueryInformationJobObject(g->job[i], JobObjectBasicAccountingInformation, &a, (DWORD)sizeof(a), NULL)) return pg_last();
        if (a.ActiveProcesses != 0) return ERROR_BUSY;
    }
    for (i = 0; i < g->processes; ++i) {
        DWORD wait = WaitForSingleObject(g->process[i], 0);
        if (wait != WAIT_OBJECT_0) return wait == WAIT_FAILED ? pg_last() : ERROR_BUSY;
    }
    return ERROR_SUCCESS;
}

PG_API PG_Create(const BYTE *sid, DWORD sid_bytes, PG_OWNER **owner) {
    PG_OWNER *g;
    DWORD error, i, j;
    SID_IDENTIFIER_AUTHORITY package = SECURITY_APP_PACKAGE_AUTHORITY;
    if (owner == NULL) return ERROR_INVALID_PARAMETER;
    *owner = NULL;
    if (!pg_ci() || sid == NULL || sid_bytes != 40 || sid[0] != SID_REVISION || sid[1] != 8 ||
        !IsValidSid((PSID)sid) || GetLengthSid((PSID)sid) != sid_bytes ||
        memcmp(GetSidIdentifierAuthority((PSID)sid), &package, sizeof(package)) != 0 ||
        *GetSidSubAuthorityCount((PSID)sid) != 8 || *GetSidSubAuthority((PSID)sid, 0) != SECURITY_APP_PACKAGE_BASE_RID) return ERROR_INVALID_SID;
    g = (PG_OWNER *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(*g));
    if (g == NULL) return ERROR_NOT_ENOUGH_MEMORY;
    g->magic = PG_MAGIC; g->pid = GetCurrentProcessId(); g->tid = GetCurrentThreadId(); g->state = PG_NEW;
    g->sid_bytes = sid_bytes;
    if (!CopySid(SECURITY_MAX_SID_SIZE, g->sid, (PSID)sid)) { error = pg_last(); goto failed; }
    if (CoCreateGuid(&g->sublayer) != S_OK) { error = ERROR_GEN_FAILURE; goto failed; }
    for (i = 0; i < 4; ++i) {
        if (CoCreateGuid(&g->filters[i]) != S_OK || pg_guid_equal(&g->filters[i], &g->sublayer)) { error = ERROR_GEN_FAILURE; goto failed; }
        for (j = 0; j < i; ++j) if (pg_guid_equal(&g->filters[i], &g->filters[j])) { error = ERROR_GEN_FAILURE; goto failed; }
    }
    error = pg_security(g);
    if (error != ERROR_SUCCESS) goto failed;
    *owner = g;
    return ERROR_SUCCESS;
failed:
    SecureZeroMemory(g, sizeof(*g)); HeapFree(GetProcessHeap(), 0, g);
    return error;
}
PG_API PG_GetInfo(PG_OWNER *g, PG_INFO *info, DWORD bytes) {
    DWORD error = pg_valid(g);
    if (error != ERROR_SUCCESS) return error;
    if (info == NULL || bytes != sizeof(*info)) return ERROR_BAD_LENGTH;
    ZeroMemory(info, sizeof(*info));
    info->abi = PG_ABI; info->bytes = (DWORD)sizeof(*info); info->state = g->state; info->poisoned = g->poisoned;
    info->sublayer = g->sublayer; memcpy(info->filters, g->filters, sizeof(info->filters));
    info->sid_bytes = g->sid_bytes; memcpy(info->sid, g->sid, g->sid_bytes);
    info->jobs = g->jobs; info->processes = g->processes; info->policy_may_exist = g->policy_may_exist;
    info->last_error = g->last_error; info->abort_error = g->abort_error;
    info->pending_create = g->pending_create; info->pending_job = g->pending_job;
    return ERROR_SUCCESS;
}
PG_API PG_Arm(PG_OWNER *g) {
    FWPM_SESSION0 session;
    FWPM_SUBLAYER0 sub;
    DWORD error, i;
    BOOL transaction = FALSE;
    if (pg_valid(g) != ERROR_SUCCESS) return ERROR_INVALID_HANDLE;
    if (g->poisoned || g->state != PG_NEW) return pg_fail(g, ERROR_INVALID_STATE);
    ZeroMemory(&session, sizeof(session)); session.txnWaitTimeoutInMSec = 2000;
    error = FwpmEngineOpen0(NULL, RPC_C_AUTHN_WINNT, NULL, &session, &g->engine);
    if (error != ERROR_SUCCESS) return pg_fail(g, error);
    error = FwpmTransactionBegin0(g->engine, 0);
    if (error != ERROR_SUCCESS) return pg_fail(g, error);
    transaction = TRUE;
    ZeroMemory(&sub, sizeof(sub)); sub.subLayerKey = g->sublayer;
    sub.displayData.name = L"KiCad Autorouter fresh-SID canary";
    sub.flags = FWPM_SUBLAYER_FLAG_PERSISTENT; sub.weight = 0x7f00;
    g->policy_may_exist = 1; /* Conservative after any policy mutation attempt. */
    error = FwpmSubLayerAdd0(g->engine, &sub, &g->security);
    for (i = 0; error == ERROR_SUCCESS && i < 4; ++i) {
        FWPM_FILTER0 f;
        FWPM_FILTER_CONDITION0 condition;
        ZeroMemory(&f, sizeof(f)); ZeroMemory(&condition, sizeof(condition));
        f.filterKey = g->filters[i]; f.displayData.name = L"KiCad Autorouter fresh-SID deny";
        f.flags = FWPM_FILTER_FLAG_PERSISTENT; f.layerKey = *pg_layers[i]; f.subLayerKey = g->sublayer;
        f.weight.type = FWP_UINT8; f.weight.uint8 = 15;
        condition.fieldKey = FWPM_CONDITION_ALE_PACKAGE_ID; condition.matchType = FWP_MATCH_EQUAL;
        condition.conditionValue.type = FWP_SID; condition.conditionValue.sid = (SID *)g->sid;
        f.numFilterConditions = 1; f.filterCondition = &condition; f.action.type = FWP_ACTION_BLOCK;
        error = FwpmFilterAdd0(g->engine, &f, &g->security, NULL);
    }
    if (error == ERROR_SUCCESS) {
        /* A failed/ambiguous commit may have persisted policy. Never clean it
         * merely because this call returned an error or the session closes. */
        g->policy_may_exist = 1;
        error = FwpmTransactionCommit0(g->engine);
        if (error == ERROR_SUCCESS) transaction = FALSE;
    }
    if (error == ERROR_SUCCESS) error = pg_check_policy(g);
    if (error != ERROR_SUCCESS) {
        if (transaction) g->abort_error = FwpmTransactionAbort0(g->engine);
        return pg_fail(g, error);
    }
    g->state = PG_ARMED;
    return ERROR_SUCCESS;
}
PG_API PG_CheckArmed(PG_OWNER *g) {
    DWORD error = pg_valid(g);
    if (error != ERROR_SUCCESS) return error;
    if (g->poisoned || g->state != PG_ARMED) return pg_fail(g, ERROR_INVALID_STATE);
    error = pg_check_policy(g);
    return error == ERROR_SUCCESS ? ERROR_SUCCESS : pg_fail(g, error);
}
PG_API PG_RegisterJob(PG_OWNER *g, HANDLE job, DWORD *slot) {
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits;
    HANDLE copy = NULL;
    DWORD error = PG_CheckArmed(g);
    if (error != ERROR_SUCCESS) return error;
    if (slot == NULL || g->jobs >= PG_JOBS || job == NULL || job == INVALID_HANDLE_VALUE) return pg_fail(g, ERROR_INVALID_PARAMETER);
    ZeroMemory(&limits, sizeof(limits));
    if (!QueryInformationJobObject(job, JobObjectExtendedLimitInformation, &limits, (DWORD)sizeof(limits), NULL)) return pg_fail(g, pg_last());
    if ((limits.BasicLimitInformation.LimitFlags & JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE) == 0 ||
        (limits.BasicLimitInformation.LimitFlags & (JOB_OBJECT_LIMIT_BREAKAWAY_OK | JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK)) != 0) return pg_fail(g, ERROR_INVALID_DATA);
    if (!DuplicateHandle(GetCurrentProcess(), job, GetCurrentProcess(), &copy, 0, FALSE, DUPLICATE_SAME_ACCESS)) return pg_fail(g, pg_last());
    *slot = g->jobs; g->job[g->jobs++] = copy;
    return ERROR_SUCCESS;
}
PG_API PG_BeginCreate(PG_OWNER *g, DWORD job_slot) {
    DWORD error = PG_CheckArmed(g);
    if (error != ERROR_SUCCESS) return error;
    if (g->pending_create || job_slot >= g->jobs || g->processes >= PG_PROCESSES)
        return pg_fail(g, ERROR_INVALID_PARAMETER);
    /* Must precede EVERY fallible CreateProcess call. There is intentionally
     * no cancel/reset operation: failure or uncertain registration orphans it. */
    g->pending_create = 1; g->pending_job = job_slot;
    return ERROR_SUCCESS;
}
PG_API PG_Poison(PG_OWNER *g, DWORD reason) {
    DWORD error = pg_valid(g);
    if (error != ERROR_SUCCESS) return error;
    (void)pg_fail(g, reason);
    return ERROR_SUCCESS; /* The poison operation succeeded, never admission. */
}
PG_API PG_RegisterProcess(PG_OWNER *g, DWORD job_slot, HANDLE process, DWORD *slot) {
    HANDLE copy = NULL;
    DWORD error = pg_valid(g);
    if (error != ERROR_SUCCESS) return error;
    if (g->poisoned || g->state != PG_ARMED || slot == NULL || !g->pending_create || g->pending_job != job_slot ||
        job_slot >= g->jobs || g->processes >= PG_PROCESSES ||
        process == NULL || process == INVALID_HANDLE_VALUE) return pg_fail(g, ERROR_INVALID_PARAMETER);
    if (!DuplicateHandle(GetCurrentProcess(), process, GetCurrentProcess(), &copy, 0, FALSE, DUPLICATE_SAME_ACCESS)) return pg_fail(g, pg_last());
    /* Own the duplicate even on type-check failure. A signaled thread/event
     * is not a process-death proof and must never clear the creation latch. */
    g->process_job[g->processes] = job_slot;
    g->process[g->processes++] = copy;
    if (GetProcessId(copy) == 0) return pg_fail(g, pg_last());
    *slot = g->processes - 1; g->pending_create = 0;
    /* Retain first, then perform policy queries. A failed query poisons this
     * live owner while keeping the actual process handle and no cleanup path. */
    return PG_CheckArmed(g);
}
PG_API PG_BeforeResume(PG_OWNER *g, DWORD process_slot) {
    BOOL member = FALSE;
    DWORD error = PG_CheckArmed(g);
    if (error != ERROR_SUCCESS) return error;
    if (g->pending_create || process_slot >= g->processes || g->resume_checked[process_slot]) return pg_fail(g, ERROR_INVALID_PARAMETER);
    if (!IsProcessInJob(g->process[process_slot], g->job[g->process_job[process_slot]], &member)) return pg_fail(g, pg_last());
    if (!member) return pg_fail(g, ERROR_INVALID_DATA);
    /* Existing typed Python AppContainer guard must still check the suspended
     * token SID/capabilities and exact source/tool/ACL contract before resume. */
    g->resume_checked[process_slot] = 1;
    return ERROR_SUCCESS;
}
PG_API PG_SealLaunches(PG_OWNER *g) {
    DWORD error = PG_CheckArmed(g);
    if (error != ERROR_SUCCESS) return error;
    if (g->pending_create) return pg_fail(g, ERROR_INVALID_STATE);
    g->state = PG_SEALED;
    return ERROR_SUCCESS;
}
PG_API PG_RemoveWhenEmpty(PG_OWNER *g) {
    HANDLE observer = NULL;
    DWORD error = pg_valid(g), i;
    BOOL transaction = FALSE;
    if (error != ERROR_SUCCESS) return error;
    if (g->poisoned || g->pending_create || g->state != PG_SEALED) return pg_fail(g, ERROR_INVALID_STATE);
    error = FwpmTransactionBegin0(g->engine, 0);
    if (error == ERROR_SUCCESS) transaction = TRUE;
    if (error == ERROR_SUCCESS) error = pg_check_policy(g);
    /* Last live identity fence before deletion, after all policy/security
     * callbacks. Saved ZERO receipts and PID absence are never consulted. */
    if (error == ERROR_SUCCESS) error = pg_empty(g);
    for (i = 0; error == ERROR_SUCCESS && i < 4; ++i) error = FwpmFilterDeleteByKey0(g->engine, &g->filters[i]);
    if (error == ERROR_SUCCESS) error = FwpmSubLayerDeleteByKey0(g->engine, &g->sublayer);
    if (error == ERROR_SUCCESS) {
        error = FwpmTransactionCommit0(g->engine);
        if (error == ERROR_SUCCESS) transaction = FALSE;
    }
    if (error == ERROR_SUCCESS) error = FwpmEngineOpen0(NULL, RPC_C_AUTHN_WINNT, NULL, NULL, &observer);
    for (i = 0; error == ERROR_SUCCESS && i < 4; ++i) {
        FWPM_FILTER0 *f = NULL;
        DWORD found = FwpmFilterGetByKey0(observer, &g->filters[i], &f);
        if (f != NULL) FwpmFreeMemory0((void **)&f);
        if (found != (DWORD)FWP_E_FILTER_NOT_FOUND) error = found == ERROR_SUCCESS ? ERROR_ALREADY_EXISTS : found;
    }
    if (error == ERROR_SUCCESS) {
        FWPM_SUBLAYER0 *sub = NULL;
        DWORD found = FwpmSubLayerGetByKey0(observer, &g->sublayer, &sub);
        if (sub != NULL) FwpmFreeMemory0((void **)&sub);
        if (found != (DWORD)FWP_E_SUBLAYER_NOT_FOUND) error = found == ERROR_SUCCESS ? ERROR_ALREADY_EXISTS : found;
    }
    if (observer != NULL) {
        DWORD close_error = FwpmEngineClose0(observer);
        if (error == ERROR_SUCCESS) error = close_error;
    }
    if (error != ERROR_SUCCESS) {
        if (transaction) g->abort_error = FwpmTransactionAbort0(g->engine);
        return pg_fail(g, error);
    }
    g->policy_may_exist = 0; g->state = PG_REMOVED;
    return ERROR_SUCCESS;
}
PG_API PG_AbandonAndFree(PG_OWNER **owner) {
    PG_OWNER *g;
    DWORD error, i, first = ERROR_SUCCESS;
    if (owner == NULL) return ERROR_INVALID_PARAMETER;
    g = *owner; error = pg_valid(g);
    if (error != ERROR_SUCCESS) return error;
    /* Intentionally NO filter/sublayer/profile deletion or journal mutation.
     * Closing this non-dynamic engine does not remove persistent objects. */
    if (g->engine != NULL) first = FwpmEngineClose0(g->engine);
    for (i = 0; i < g->processes; ++i) if (!CloseHandle(g->process[i]) && first == ERROR_SUCCESS) first = pg_last();
    for (i = 0; i < g->jobs; ++i) if (!CloseHandle(g->job[i]) && first == ERROR_SUCCESS) first = pg_last();
    g->magic = 0; SecureZeroMemory(g, sizeof(*g));
    if (!HeapFree(GetProcessHeap(), 0, g) && first == ERROR_SUCCESS) first = pg_last();
    *owner = NULL;
    return first;
}
