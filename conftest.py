# conftest.py — pytest root configuration
#
# Exclude integration scripts that require real Google Drive API credentials
# (google-auth / google-api-python-client). These are operational scripts,
# not unit tests, and cannot run without external service credentials.
collect_ignore = [
    "scripts/rodada_4_31b_drive_api_oauth_real_test.py",
    "scripts/rodada_4_33_operational_controlled_input_test.py",
]
