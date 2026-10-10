"""Create a disposable project for manual GUI review without modifying a receipt."""
from pathlib import Path
import shutil
from .pipeline import Rejected, check_result, tree_hash, save_json, sha


def review_copy(receipt, output):
    receipt = Path(receipt).resolve(strict=True)
    receipt_digest = sha(receipt)
    verified = check_result(receipt)
    if verified.get('input_policy') == 'board-floors-v1':
        raise Rejected('floor-policy GUI handoff is not yet qualified')
    candidate = Path(verified['candidate'])
    destination = Path(output).absolute()
    if destination.exists() or destination.is_symlink():
        raise Rejected('review output already exists')
    if any(p.is_symlink() for p in destination.parents):
        raise Rejected('review output has a symlink ancestor')
    destination = destination.resolve()
    # A review may cause KiCad to create history/settings files. Keep it outside
    # both the source project and the complete evidence run.
    import json
    report = json.loads(receipt.read_text())
    for protected in (Path(report['source']).resolve().parent, receipt.parent):
        if destination == protected or protected in destination.parents:
            raise Rejected('review copy must be outside source and evidence directories')
    before = tree_hash(candidate.parent)
    destination.mkdir(parents=True, exist_ok=False)
    project = destination / 'project'
    shutil.copytree(candidate.parent, project)
    if tree_hash(project) != before or tree_hash(candidate.parent) != before:
        raise Rejected('candidate changed while preparing review copy')
    rechecked = check_result(receipt)
    if sha(receipt) != receipt_digest or any(rechecked.get(k) != verified.get(k) for k in ('candidate', 'candidate_sha256')) or sha(project / candidate.name) != verified['candidate_sha256']:
        raise Rejected('receipt or candidate changed while preparing review copy')
    record = {'schema': 1, 'status': 'ready_for_manual_review', 'receipt': str(receipt),
              'receipt_sha256': receipt_digest, 'candidate_sha256': sha(project / candidate.name),
              'project': str(project), 'board': str(project / candidate.name),
              'initial_project_hashes': before,
              'limits': 'This is a disposable review copy, not an applied result. KiCad may rewrite project settings even when board changes are discarded. Any saved edit invalidates the original validation claim. No live-board replacement, automatic approval, GUI stale-edit detection or undo is implemented.'}
    save_json(destination / 'review.json', record)
    return record
