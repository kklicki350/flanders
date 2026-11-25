from flanders.workspace.models import Run, RunStatus


def nav(request):
    return {
        "active_run": Run.objects.filter(status=RunStatus.RUNNING).first(),
        "interrupted_runs": Run.objects.filter(status=RunStatus.INTERRUPTED)[:3],
    }
