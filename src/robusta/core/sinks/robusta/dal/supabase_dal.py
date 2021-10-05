import base64
import json
import logging
import threading
import time
import traceback
import uuid
import requests
import datetime

from typing import List, Dict, Any

from supabase_py.lib.auth_client import SupabaseAuthClient

from ...transformer import Transformer
from ....discovery.top_service_resolver import TopServiceResolver
from ....model.services import ServiceInfo
from ....reporting.blocks import (
    Finding,
    Enrichment,
    MarkdownBlock,
    KubernetesDiffBlock,
    DividerBlock,
    FileBlock,
    HeaderBlock,
    CallbackBlock,
    ListBlock,
    TableBlock,
)
from ....model.env_vars import TARGET_ID, SUPABASE_LOGIN_RATE_LIMIT_SEC
from ....reporting.callbacks import PlaybookCallbackRequest
from supabase_py import Client

SERVICES_TABLE = "Services"
EVIDENCE_TABLE = "Evidence"
ISSUES_TABLE = "Issues"


class RobustaAuthClient(SupabaseAuthClient):
    def _set_timeout(*args, **kwargs):
        """Set timer task"""
        # _set_timeout isn't implemented in gotrue client. it's required for the jwt refresh token timer task
        # https://github.com/supabase/gotrue-py/blob/49c092e3a4a6d7bb5e1c08067a4c42cc2f74b5cc/gotrue/client.py#L242
        # callback, timeout_ms
        threading.Timer(args[2] / 1000, args[1]).start()


class RobustaClient(Client):
    def _get_auth_headers(self) -> Dict[str, str]:
        auth = getattr(self, "auth", None)
        session = auth.current_session if auth else None
        if session and session["access_token"]:
            access_token = auth.session()["access_token"]
        else:
            access_token = self.supabase_key

        headers: Dict[str, str] = {
            "apiKey": self.supabase_key,
            "Authorization": f"Bearer {access_token}",
        }
        return headers

    @staticmethod
    def _init_supabase_auth_client(
        auth_url: str,
        supabase_key: str,
        detect_session_in_url: bool,
        auto_refresh_token: bool,
        persist_session: bool,
        local_storage: Dict[str, Any],
        headers: Dict[str, str],
    ) -> RobustaAuthClient:
        """Creates a wrapped instance of the GoTrue Client."""
        return RobustaAuthClient(
            url=auth_url,
            auto_refresh_token=auto_refresh_token,
            detect_session_in_url=detect_session_in_url,
            persist_session=persist_session,
            local_storage=local_storage,
            headers=headers,
        )

    def rpc(self, fn, params):
        """Similar to _execute_monkey_patch in supabase-py - we make the async rpc call sync"""
        path = f"rpc/{fn}"
        url: str = str(self.postgrest.session.base_url).rstrip("/")
        query: str = str(self.postgrest.session.params)
        response = requests.post(
            f"{url}/{path}?{query}",
            headers=dict(self.postgrest.session.headers) | self._get_auth_headers(),
            json=params,
        )
        return {
            "data": response.json(),
            "status_code": response.status_code,
        }


class SupabaseDal:
    def __init__(
        self,
        url: str,
        key: str,
        account_id: str,
        email: str,
        password: str,
        sink_name: str,
        cluster_name: str,
    ):
        self.url = url
        self.key = key
        self.account_id = account_id
        self.cluster = cluster_name
        self.client = RobustaClient(url, key)
        self.email = email
        self.password = password
        self.sign_in_time = 0
        self.sign_in()
        self.target_id = TARGET_ID
        self.sink_name = sink_name

    def to_issue(self, finding: Finding):
        return {
            "name": finding.aggregation_key,
            "account_id": self.account_id,
            "priority": finding.severity.name,
            "service_key": TopServiceResolver.guess_service_key(
                finding.subject.name, finding.subject.namespace
            ),
            "source": finding.source.value,
            "category": finding.finding_type.value,
            "fingerprint": finding.fingerprint,
            "title": finding.title,
            "start_date": datetime.datetime.utcnow().isoformat(),
            "end_date": None,
            "description": finding.description,
            "is_failure": finding.failure,
            "subject_type": finding.subject.subject_type.value,
            "subject_name": finding.subject.name,
            "subject_namespace": finding.subject.namespace,
            "subject_cluster": self.cluster,
        }

    def to_evidence(self, finding_id: uuid, enrichment: Enrichment) -> Dict[Any, Any]:
        structured_data = []
        for block in enrichment.blocks:
            if isinstance(block, MarkdownBlock):
                if not block.text:
                    continue
                structured_data.append(
                    {
                        "type": "markdown",
                        "data": Transformer.to_github_markdown(block.text),
                    }
                )
            elif isinstance(block, DividerBlock):
                structured_data.append({"type": "divider"})
            elif isinstance(block, FileBlock):
                last_dot_idx = block.filename.rindex(".")
                structured_data.append(
                    {
                        "type": block.filename[last_dot_idx + 1 :],
                        "data": str(base64.b64encode(block.contents)),
                    }
                )
            elif isinstance(block, HeaderBlock):
                structured_data.append({"type": "header", "data": block.text})
            elif isinstance(block, ListBlock):
                structured_data.append({"type": "list", "data": block.items})
            elif isinstance(block, TableBlock):
                structured_data.append(
                    {
                        "type": "table",
                        "data": {
                            "headers": block.headers,
                            "rows": [row for row in block.rows],
                            "column_renderers": block.column_renderers,
                        },
                    }
                )
            elif isinstance(block, KubernetesDiffBlock):
                structured_data.append(
                    {
                        "type": "diff",
                        "data": {
                            "old": block.old,
                            "new": block.new,
                            "resource_name": block.resource_name,
                            "num_additions": block.num_additions,
                            "num_deletions": block.num_deletions,
                            "num_modifications": block.num_modifications,
                            "updated_paths": [d.formatted_path for d in block.diffs],
                        },
                    }
                )
            elif isinstance(block, CallbackBlock):
                context = block.context.copy()
                context["target_id"] = self.target_id
                context["sink_name"] = self.sink_name
                callbacks = []
                for (text, callback) in block.choices.items():
                    callbacks.append(
                        {
                            "text": text,
                            "callback": PlaybookCallbackRequest.create_for_func(
                                callback, json.dumps(context), text
                            ).json(),
                        }
                    )

                structured_data.append({"type": "callbacks", "data": callbacks})
            else:
                logging.error(
                    f"cannot convert block of type {type(block)} to robusta platform format block: {block}"
                )
                continue  # no reason to crash the entire report

        return {
            "finding_id": str(finding_id),
            "data": json.dumps(structured_data),
            "account_id": self.account_id,
            "category": enrichment.category and enrichment.category.value,
        }

    def persist_finding(self, finding: Finding):
        res = self.client.rpc("insert_finding_v1", self.to_issue(finding))
        if res.get("status_code") not in [200, 201]:
            logging.error(
                f"Failed to persist finding={finding} error: {res.get('data')}. Dropping Finding"
            )
            self.handle_supabase_error()
            return
        res_data = res.get("data")[0]
        finding_id = res_data.get("id")
        new_finding = res_data.get("inserted")
        if not new_finding:
            logging.info(
                f"this finding already exists in supabase; updating existing; finding={finding}"
            )

        for enrichment in finding.enrichments:
            res = self.client.rpc(
                "insert_enrichment_v1", self.to_evidence(finding_id, enrichment)
            )
            if res.get("status_code") not in [200, 201]:
                logging.error(
                    f"Failed to persist enrichment; finding={finding} enrichment={enrichment} error: {res.get('data')}. Dropping enrichment"
                )

    def to_service(self, service: ServiceInfo) -> Dict[Any, Any]:
        return {
            "name": service.name,
            "type": service.service_type,
            "namespace": service.namespace,
            "classification": service.classification,
            "cluster": self.cluster,
            "account_id": self.account_id,
            "deleted": service.deleted,
            "service_key": service.get_service_key(),
            "update_time": "now()",
        }

    def persist_service(self, service: ServiceInfo):
        db_service = self.to_service(service)
        res = (
            self.client.table(SERVICES_TABLE).insert(db_service, upsert=True).execute()
        )
        if res.get("status_code") not in [200, 201]:
            logging.error(
                f"Failed to persist service {service} error: {res.get('data')}"
            )
            self.handle_supabase_error()

    def get_active_services(self) -> List[ServiceInfo]:
        res = (
            self.client.table(SERVICES_TABLE)
            .select("name", "type", "namespace", "classification")
            .filter("account_id", "eq", self.account_id)
            .filter("cluster", "eq", self.cluster)
            .filter("deleted", "eq", False)
            .execute()
        )
        if res.get("status_code") not in [200]:
            msg = f"Failed to get existing services (supabase) error: {res.get('data')}"
            logging.error(msg)
            self.handle_supabase_error()
            raise Exception(msg)

        return [
            ServiceInfo(
                name=service["name"],
                service_type=service["type"],
                namespace=service["namespace"],
                classification=service["classification"],
            )
            for service in res.get("data")
        ]

    def sign_in(self):
        if time.time() > self.sign_in_time + SUPABASE_LOGIN_RATE_LIMIT_SEC:
            logging.info("Supabase dal login")
            self.sign_in_time = time.time()
            self.client.auth.sign_in(email=self.email, password=self.password)

    def handle_supabase_error(self):
        """Workaround for Gotrue bug in refresh token."""
        # If there's an error during refresh token, no new refresh timer task is created, and the client remains not authenticated for good
        # When there's an error connecting to supabase server, we will re-login, to re-authenticate the session.
        # Adding rate-limiting mechanism, not to login too much because of other errors
        # https://github.com/supabase/gotrue-py/issues/9
        try:
            self.sign_in()
        except Exception as e:
            logging.error("Failed to signin on error", traceback.print_exc())
