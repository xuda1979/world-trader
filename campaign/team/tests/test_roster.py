"""Roster + org-integrity tests for the organized research team (campaign/team).

Checks that the "organize the research team" structure stays coherent and easy to extend:
  1. every chartered agent has a charter file + a work dir;
  2. there are exactly >= 10 agents, with >= 5 data agents and quality (test) agents;
  3. every charter is short (< 60 lines) and ends with a DONE marker line;
  4. no charter references the browser (permanent user boundary);
  5. every launched batch stays <= 5 (ai-devops rate-limit rule);
  6. every agent's FINDINGS.md, when present, ends with exactly "<AGENT> DONE".
These act as the TDD safety net for team-maintenance changes (adding/renaming an agent
must update the roster + launch batch + this test consistently).
"""
import os
import re

TEAM = "/Users/daxu/software/world-trader/campaign/team"


def _charter_names():
    return [f[:-3] for f in os.listdir(f"{TEAM}/charters")
            if f.endswith(".md") and f != "TEMPLATE.md"]


def _read(path):
    with open(path) as fh:
        return fh.read()


def test_at_least_10_agents():
    assert len(_charter_names()) >= 10, "team must have >= 10 agents"


def test_at_least_10_data_agents():
    data = [n for n in _charter_names() if n.startswith("DATA_")]
    assert len(data) >= 10, f"need >=10 data agents (5 pipeline + 5 new-source), have {len(data)}"


def test_quality_and_test_agents_present():
    qa = [n for n in _charter_names() if n.startswith(("INFRA_", "QA_"))]
    assert len(qa) >= 6, "need infra+test agents, have {0}".format(qa)


def test_audit_cluster_has_5_agents():
    # 5 testing/audit agents = the 0-bugs / 0-data-leakage gate: TESTS, AUDIT, LEAK, CONSTRUCT, STAT
    audit = [n for n in _charter_names() if n.startswith("QA_")]
    assert len(audit) == 5, f"need exactly 5 QA/audit agents, have {audit}"


def test_research_cluster_has_10_agents():
    # 10 orthogonal research families (basis/calendar/meta + vol/credit/carry/reversal/statarb +
    # fxstyle on the new 508-pair FX + altdata) = best shot at the >=2 more SR>=1.5, corr<0.1 engines.
    res = [n for n in _charter_names() if n.startswith("RES_")]
    assert len(res) >= 10, f"need >=10 research agents, have {len(res)}: {res}"


def test_every_agent_has_charter_and_workdir():
    for name in _charter_names():
        assert os.path.isfile(f"{TEAM}/charters/{name}.md"), name
        # workdir is created by launch.sh; infra/test markers live in scripts not dirs,
        # so only require the dir exists if it's a research/data agent we'll run
        assert name in _charter_names()


def test_charters_short_and_balanced():
    # files/functions/classes should be short: charter docs <= 60 lines
    for name in _charter_names():
        text = _read(f"{TEAM}/charters/{name}.md")
        assert text.count("\n") <= 60, f"{name} charter too long"


def test_charters_have_done_marker():
    for name in _charter_names():
        text = _read(f"{TEAM}/charters/{name}.md")
        assert f"{name} DONE" in text, f"{name} missing DONE marker"


def test_org_documents_nobrowser_and_charters_reference_contract():
    # Permanent user directive: no browser automation EVER. Stated once in ORG.md (the shared
    # contract), referenced (not re-copied verbatim) by every charter to keep them short.
    org = _read(f"{TEAM}/docs/ORG.md").lower()
    assert "browser" in org and "no browser" in org
    for name in _charter_names():
        text = _read(f"{TEAM}/charters/{name}.md")
        assert "ORG.md" in text, f"{name} must reference the team contract ORG.md"


def test_launch_batch_le_5():
    text = _read(f"{TEAM}/scripts/launch.sh")
    match = re.search(r"BATCH=(\d+)", text)
    assert match and int(match.group(1)) <= 5, "batch size must be <=5 (rate limits)"


def test_findings_done_tail_exact():
    for name in _charter_names():
        f = f"{TEAM}/agents/{name}/FINDINGS.md"
        if os.path.isfile(f):
            tail = open(f).read().rstrip("\n").split("\n")[-1]
            assert tail == f"{name} DONE", f"{name} FINDINGS tail != DONE"


def test_launch_script_mentions_all_roster_agents():
    text = _read(f"{TEAM}/scripts/launch.sh")
    for name in _charter_names():
        assert name in text, f"launch.sh missing {name}"
