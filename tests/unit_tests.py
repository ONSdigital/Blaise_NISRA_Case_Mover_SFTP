from unittest import mock
from unittest.mock import patch

import pytest

from blaise_nisra_case_mover import *


@pytest.fixture
def mock_sftp():
    return mock.MagicMock()


def test_get_instrument_folders(mock_sftp):
    mock_sftp.listdir.return_value = ["OPN2101A", "LMS2101A", "foobar"]
    assert get_instrument_folders(mock_sftp, "") == ["OPN2101A", "LMS2101A"]


def test_get_instrument_files(mock_sftp):
    mock_sftp.listdir.return_value = ["OPN2101A.bdbx",
                                      "OPN2101A.bdix",
                                      "OPN2101A.bmix",
                                      "OPN2101A.pdf",
                                      "FrameSOC.blix",
                                      ]
    assert get_instrument_files(mock_sftp, "") == [
        "OPN2101A.bdbx",
        "OPN2101A.bdix",
        "OPN2101A.bmix",
        "FrameSOC.blix",
    ]


def test_check_instrument_database_file_exists_returns_false_if_file_list_is_empty():
    file_list = []
    instrument_name = "OPN2101A"
    assert check_instrument_database_file_exists(file_list, instrument_name) is False


def test_check_instrument_database_file_exists_returns_false_if_no_instrument_database_file_found():
    file_list = ["OPN2101A.bdix", "OPN2101A.bmix", "FrameSOC.blix"]
    instrument_name = "OPN2101A"
    assert check_instrument_database_file_exists(file_list, instrument_name) is False


def test_check_instrument_database_file_exists_returns_false_if_different_database_file_found():
    file_list = ["LMS2101A.bdbx", "LMS2101A.bdix", "LMS2101A.bmix", "FrameSOC.blix"]
    instrument_name = "OPN2101A"
    assert check_instrument_database_file_exists(file_list, instrument_name) is False


def test_check_instrument_database_file_exists_returns_true_if_correct_instrument_database_file_found():
    file_list = ["oPn2101A.bDbX", "OPN2101A.bdix", "OPN2101A.bmix", "FrameSOC.blix"]
    instrument_name = "OPN2101A"
    assert check_instrument_database_file_exists(file_list, instrument_name) is True


@patch.object(GoogleStorage, "get_blob", return_value=None)
def test_check_if_matching_file_in_bucket_returns_false_if_no_files_in_bucket(mock_get_blob):
    assert check_if_matching_file_in_bucket("OPN2101A.bdbx", "OPN2101A/OPN2101A.bdbx") is False


@patch.object(GoogleStorage, "get_blob")
@patch.object(hashlib, "md5")
@patch("builtins.open")
def test_check_if_matching_file_in_bucket_returns_true_if_files_match(mock_open, mock_hashlib, mock_get_blob):
    mock_md5 = mock.MagicMock()
    mock_md5.digest.return_value = b"123456789"
    mock_hashlib.return_value = mock_md5
    mock_get_blob.return_value = mock.MagicMock(md5_hash=pybase64.b64encode(b"123456789"), name="OPN2101A")
    assert check_if_matching_file_in_bucket("OPN2101A.bdbx", "OPN2101A/OPN2101A.bdbx") is True


@patch.object(GoogleStorage, "get_blob")
@patch.object(hashlib, "md5")
@patch("builtins.open")
def test_check_if_matching_file_in_bucket_returns_false_if_files_do_not_match(mock_open, mock_hashlib, mock_get_blob):
    mock_md5 = mock.MagicMock()
    mock_md5.digest.return_value = "987654321"
    mock_hashlib.return_value = mock_md5
    mock_get_blob.return_value = mock.MagicMock(md5_hash=pybase64.b64encode(b"123456789"), name="OPN2101A")
    assert check_if_matching_file_in_bucket("OPN2101A.bdbx", "OPN2101A/OPN2101A.bdbx") is False


@patch("blaise_nisra_case_mover.delete_local_instrument_files")
@patch("blaise_nisra_case_mover.get_instrument_files")
@patch("blaise_nisra_case_mover.check_if_matching_file_in_bucket")
@patch("blaise_nisra_case_mover.upload_instrument")
def test_process_instrument_if_no_instrument_files(
        mock_upload_instrument,
        mock_check_if_matching_file_in_bucket,
        mock_get_instrument_files,
        mock_delete_local_instrument_files,
        mock_sftp,
):
    mock_get_instrument_files.return_value = []
    assert (process_instrument(mock_sftp, "ONS/OPN/OPN2101A/")
            == "No instrument files found in folder - ONS/OPN/OPN2101A/"
            )
    mock_delete_local_instrument_files.assert_called_once()
    mock_check_if_matching_file_in_bucket.assert_not_called()
    mock_upload_instrument.assert_not_called()


@patch("blaise_nisra_case_mover.delete_local_instrument_files")
@patch("blaise_nisra_case_mover.get_instrument_files")
@patch("blaise_nisra_case_mover.check_if_matching_file_in_bucket")
@patch("blaise_nisra_case_mover.upload_instrument")
def test_process_instrument_if_no_instrument_database_file(
        mock_upload_instrument,
        mock_check_if_matching_file_in_bucket,
        mock_get_instrument_files,
        mock_delete_local_instrument_files,
        mock_sftp,
):
    mock_get_instrument_files.return_value = [
        "OPN2101A.bdix",
        "OPN2101A.bmix",
        "FrameSOC.blix",
        "foobar.bdbx",
    ]
    assert (
            process_instrument(mock_sftp, "ONS/OPN/OPN2101A/")
            == "Instrument database file not found - OPN2101A.bdbx"
    )
    mock_delete_local_instrument_files.assert_called_once()
    mock_check_if_matching_file_in_bucket.assert_not_called()
    mock_upload_instrument.assert_not_called()


@patch("blaise_nisra_case_mover.check_instrument_database_file_exists")
@patch("blaise_nisra_case_mover.delete_local_instrument_files")
@patch("blaise_nisra_case_mover.get_instrument_files")
@patch("blaise_nisra_case_mover.check_if_matching_file_in_bucket")
@patch("blaise_nisra_case_mover.upload_instrument")
def test_process_instrument_uploads_instrument_if_database_files_do_not_match(
        mock_upload_instrument,
        mock_check_if_matching_file_in_bucket,
        mock_get_instrument_files,
        mock_delete_local_instrument_files,
        mock_check_instrument_database_file_exists,
        mock_sftp,
):
    mock_get_instrument_files.return_value = [
        "OPN2101A.bdix",
        "OPN2101A.bmix",
        "OPN2101A.blix",
        "OPN2101A.bdbx",
    ]
    mock_check_instrument_database_file_exists.return_value = True
    mock_check_if_matching_file_in_bucket.return_value = False
    process_instrument(mock_sftp, "ONS/OPN/OPN2101A/")
    mock_upload_instrument.assert_called_once_with(
        mock_sftp,
        "ONS/OPN/OPN2101A/",
        "OPN2101A",
        ["OPN2101A.bdix", "OPN2101A.bmix", "OPN2101A.blix", "OPN2101A.bdbx"],
    )
    mock_delete_local_instrument_files.assert_called_once()


@patch("blaise_nisra_case_mover.check_instrument_database_file_exists")
@patch("blaise_nisra_case_mover.delete_local_instrument_files")
@patch("blaise_nisra_case_mover.get_instrument_files")
@patch("blaise_nisra_case_mover.check_if_matching_file_in_bucket")
@patch("blaise_nisra_case_mover.upload_instrument")
def test_process_instrument_doesnt_upload_instrument_if_database_files_do_match(
        mock_upload_instrument,
        mock_check_if_matching_file_in_bucket,
        mock_get_instrument_files,
        mock_delete_local_instrument_files,
        mock_check_instrument_database_file_exists,
        mock_sftp,
):
    mock_check_instrument_database_file_exists.return_value = True
    mock_check_if_matching_file_in_bucket.return_value = True
    process_instrument(mock_sftp, "ONS/OPN/OPN2101A/")
    mock_upload_instrument.assert_not_called()
    mock_get_instrument_files.assert_called_once()
    mock_delete_local_instrument_files.assert_called_once()


@patch("blaise_nisra_case_mover.send_request_to_api")
@patch.object(GoogleStorage, "upload_file")
def test_upload_instrument(mock_google_storage, mock_send_request_to_api, mock_sftp):
    mock_send_request_to_api.return_value.status_code = 200
    instrument_name = "OPN2101A"
    instrument_files = [
        "OPN2101A.bdix",
        "OPN2101A.bmix",
        "OPN2101A.blix",
        "OPN2101A.bdbx",
    ]
    upload_instrument(mock_sftp, "ONS/OPN/OPN2101A/", instrument_name, instrument_files)
    assert mock_google_storage.call_count == len(instrument_files)
    for instrument_file in instrument_files:
        mock_google_storage.assert_any_call(instrument_file, f"{instrument_name}/{instrument_file}")

    mock_send_request_to_api.assert_called_once()


@mock.patch.dict(os.environ, {"BLAISE_API_URL": "MOCK_BLAISE_API_URL"})
@mock.patch.dict(os.environ, {"SERVER_PARK": "MOCK_SERVER_PARK"})
@patch.object(requests, "post")
def test_send_request_to_api(mock_requests_post):
    send_request_to_api("OPN2101A")
    mock_requests_post.assert_called_once_with(
        "http://MOCK_BLAISE_API_URL/api/vi/serverpark/MOCK_SERVER_PARK/instruments/OPN2101A/data",
        data='{"InstrumentDataPath": "OPN2101A"}',
        headers={"content-type": "application/json"},
    )
