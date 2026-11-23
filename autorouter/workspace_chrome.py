"""Shared presentation for the native Copperpath workspace."""


def heading(control, points):
    font = control.GetFont()
    font.SetPointSize(points)
    font.MakeBold()
    control.SetFont(font)
    return control


def colours(wx):
    if wx.SystemSettings.GetAppearance().IsDark():
        return '#252E33', '#303D41', '#A3D7C8'
    return '#F2F6F5', '#FFFFFF', '#215E53'


def name_application(app):
    app.SetAppName('Copperpath')
    app.SetAppDisplayName('Copperpath')


def counts_text(findings, open_label='open'):
    warnings = findings['warnings']
    return (f"{findings['opens']} {open_label} · {findings['blocking']} blocking · "
            f"{warnings} {'warning' if warnings == 1 else 'warnings'}")
