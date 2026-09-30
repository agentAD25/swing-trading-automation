"""Offline fail-closed boundaries. No broker network I/O and no order placement."""

from swingtrade.contracts.secret_refs import DeploymentEnvironment
from swingtrade.offline.database import (
    DatabaseBinding,
    DatabaseConnectionDenied,
    bind_database_reference,
    require_local_database_connection,
)
from swingtrade.offline.environment import (
    EnvironmentBoundaryError,
    OfflineEnvironment,
    require_deployment_environment,
    resolve_offline_environment,
)
from swingtrade.offline.hosts import (
    SIM_API_URL,
    ApiHostClass,
    HostDecision,
    HostPolicyError,
    classify_api_host,
)
from swingtrade.offline.token_store import (
    CasExpectation,
    CasMutation,
    InitialTokenRecord,
    PostgresTokenStore,
    RedactedTokenRecord,
    StaleWriterRejected,
    SyntheticCiphertext,
    TokenState,
    TokenStoreError,
    create_fixture_schema,
)
from swingtrade.offline.transport import (
    OfflineTransport,
    OfflineTransportError,
    open_offline_transport,
)

__all__ = [
    "SIM_API_URL",
    "ApiHostClass",
    "CasExpectation",
    "CasMutation",
    "DatabaseBinding",
    "DatabaseConnectionDenied",
    "DeploymentEnvironment",
    "EnvironmentBoundaryError",
    "HostDecision",
    "HostPolicyError",
    "InitialTokenRecord",
    "OfflineEnvironment",
    "OfflineTransport",
    "OfflineTransportError",
    "PostgresTokenStore",
    "RedactedTokenRecord",
    "StaleWriterRejected",
    "SyntheticCiphertext",
    "TokenState",
    "TokenStoreError",
    "bind_database_reference",
    "classify_api_host",
    "create_fixture_schema",
    "open_offline_transport",
    "require_deployment_environment",
    "require_local_database_connection",
    "resolve_offline_environment",
]
