import os
import unittest
from unittest.mock import MagicMock, patch


class TestFewsMinioClientSelection(unittest.TestCase):
    @patch("app.api.tasks.FewsKafkaMessageProducer")
    @patch("app.api.tasks.KafkaMessageProducer")
    @patch("app.api.tasks.run_windninja")
    @patch("app.api.tasks.process_windninja_input")
    @patch("app.api.tasks.os.walk")
    @patch("app.api.tasks.FewsMinioClient")
    @patch("app.api.tasks.MinioClient")
    def test_process_uses_fews_client_when_flag_true(
        self,
        mock_minio,
        mock_fews_minio,
        mock_walk,
        mock_process_input,
        mock_run,
        mock_kafka,
        mock_fews_kafka,
    ):
        from app.api.tasks import process_windninja_request

        model_id = "m1"
        payload = {"modelId": model_id, "elevation_file": "input/dtm.tif", "dict_metadata": {}}

        # Avoid touching filesystem
        mock_process_input.return_value = (model_id, [], "/tmp/dtm.tif", "/tmp/cfg.cfg")
        mock_run.return_value = (0, "", "")
        mock_walk.return_value = []

        fews_client_instance = MagicMock()
        mock_fews_minio.return_value = fews_client_instance

        kafka_instance = MagicMock()
        mock_fews_kafka.return_value = kafka_instance

        process_windninja_request(model_id, payload, "v6-7", fews=True)

        mock_fews_minio.assert_called_once()
        mock_minio.assert_not_called()
        mock_fews_kafka.assert_called_once_with("v6-7")
        mock_kafka.assert_not_called()

    @patch("app.api.tasks.FewsKafkaMessageProducer")
    @patch("app.api.tasks.KafkaMessageProducer")
    @patch("app.api.tasks.run_forecast_windninja")
    @patch("app.api.tasks.process_forecast_input")
    @patch("app.api.tasks.os.walk")
    @patch("app.api.tasks.FewsMinioClient")
    @patch("app.api.tasks.MinioClient")
    def test_forecast_uses_fews_client_when_flag_true(
        self,
        mock_minio,
        mock_fews_minio,
        mock_walk,
        mock_process_input,
        mock_run,
        mock_kafka,
        mock_fews_kafka,
    ):
        from app.api.tasks import process_windninja_forecast_request

        model_id = "m2"
        payload = {"modelId": model_id, "elevation_file": "input/dtm.tif", "dict_metadata": {}}

        mock_process_input.return_value = (model_id, "/tmp/dtm.tif", "/tmp/ws.tif", "/tmp/wd.tif", "/tmp/cfg.cfg")
        mock_run.return_value = (0, "", "")
        mock_walk.return_value = []

        fews_client_instance = MagicMock()
        mock_fews_minio.return_value = fews_client_instance

        kafka_instance = MagicMock()
        mock_fews_kafka.return_value = kafka_instance

        process_windninja_forecast_request(model_id, payload, "v6-7", fews=True)

        mock_fews_minio.assert_called_once()
        mock_minio.assert_not_called()
        mock_fews_kafka.assert_called_once_with("v6-7")
        mock_kafka.assert_not_called()

    @patch("app.api.tasks.FewsKafkaMessageProducer")
    @patch("app.api.tasks.KafkaMessageProducer")
    @patch("app.api.tasks.run_windninja")
    @patch("app.api.tasks.process_windninja_input")
    @patch("app.api.tasks.os.walk")
    @patch("app.api.tasks.FewsMinioClient")
    @patch("app.api.tasks.MinioClient")
    def test_process_uses_default_clients_when_flag_false(
        self,
        mock_minio,
        mock_fews_minio,
        mock_walk,
        mock_process_input,
        mock_run,
        mock_kafka,
        mock_fews_kafka,
    ):
        from app.api.tasks import process_windninja_request

        model_id = "m3"
        payload = {"modelId": model_id, "elevation_file": "input/dtm.tif", "dict_metadata": {}}

        mock_process_input.return_value = (model_id, [], "/tmp/dtm.tif", "/tmp/cfg.cfg")
        mock_run.return_value = (0, "", "")
        mock_walk.return_value = []

        minio_client_instance = MagicMock()
        mock_minio.return_value = minio_client_instance

        kafka_instance = MagicMock()
        mock_kafka.return_value = kafka_instance

        process_windninja_request(model_id, payload, "v6-7")

        mock_minio.assert_called_once()
        mock_fews_minio.assert_not_called()
        mock_kafka.assert_called_once_with("v6-7")
        mock_fews_kafka.assert_not_called()


if __name__ == "__main__":
    unittest.main()
