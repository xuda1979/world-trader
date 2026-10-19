"""Only industry-sponsored, projected trial metadata; no contacts or locations."""

from ..models import DataError, record
import re

from . import require

FIELDS = "NCTId,OverallStatus,Phase,LastUpdatePostDate,StudyFirstPostDate,LeadSponsorName,LeadSponsorClass,EnrollmentCount,Condition"


def clinicaltrials(client, *, condition=None, study_ids=None, max_pages=5, page_size=100):
    if max_pages < 1 or not 1 <= page_size <= 1000:
        raise DataError("Invalid ClinicalTrials.gov page budget or size")
    params = {"format": "json", "pageSize": page_size, "fields": FIELDS,
              "query.term": "AREA[LeadSponsorClass]INDUSTRY"}
    if condition:
        params["query.cond"] = condition
    if study_ids:
        ids = study_ids.split(",")
        if any(not re.fullmatch(r"NCT\d{8}", value) for value in ids):
            raise DataError("Study IDs must be comma-separated NCT identifiers")
        params["filter.ids"] = study_ids
    result, tokens = [], set()
    for _ in range(max_pages):
        doc = client.get("https://clinicaltrials.gov/api/v2/studies", params=params, ttl=21600)
        for study in require(doc.payload, "studies", list):
            protocol = require(study, "protocolSection", dict)
            nct = require(require(protocol, "identificationModule", dict), "nctId", str)
            status = require(protocol, "statusModule", dict)
            sponsor = require(require(protocol, "sponsorCollaboratorsModule", dict), "leadSponsor", dict)
            if sponsor.get("class") != "INDUSTRY":
                raise DataError("ClinicalTrials.gov did not honor the industry-sponsor filter")
            design = protocol.get("designModule", {})
            updated = status.get("lastUpdatePostDateStruct", {}).get("date")
            result.append(record(doc, source="clinicaltrials", dataset="industry_studies", entity=nct,
                                 key=nct, observed=updated, data={
                                     "status": status.get("overallStatus"), "sponsor": sponsor.get("name"),
                                     "phases": design.get("phases", []),
                                     "enrollment": design.get("enrollmentInfo", {}).get("count"),
                                     "conditions": protocol.get("conditionsModule", {}).get("conditions", []),
                                     "first_posted": status.get("studyFirstPostDateStruct", {}).get("date"),
                                     "last_update_posted": updated,
                                 }))
        token = doc.payload.get("nextPageToken")
        if not token:
            return result
        if not isinstance(token, str) or token in tokens:
            raise DataError("ClinicalTrials.gov returned a repeated or invalid page token")
        tokens.add(token)
        params = {**params, "pageToken": token}
    raise DataError("ClinicalTrials.gov result exceeds max_pages; narrow --condition or increase the budget")
