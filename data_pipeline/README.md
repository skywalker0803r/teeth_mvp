# Teeth MVP Data Pipeline

這個專案是 `Teeth MVP` 的資料管道部分，它利用 Docker 和 Docker Compose 部署了一套包含 Apache Airflow、PostgreSQL、Redis 和 Apache Spark 的資料處理環境。此設定旨在提供一個可擴展且易於管理的平台，用於排程、執行和監控資料處理工作流程。

## 專案組件

*   **Apache Airflow**: (版本 2.9.2)
    *   **用途**: 工作流程管理平台，用於編排、排程和監控資料管道中的任務。
    *   **服務**: `airflow-webserver` (提供 UI 介面), `airflow-scheduler` (排程任務), `airflow-init` (初始化設定)。
*   **PostgreSQL**: (版本 13)
    *   **用途**: 作為 Airflow 的元資料庫 (Metadata Database)，儲存所有 Airflow 的配置、任務狀態和歷史記錄。
*   **Redis**:
    *   **用途**: 作為 Airflow Webserver 的快取和速率限制儲存。
*   **Apache Spark**:
    *   **用途**: 分散式資料處理引擎，用於執行大規模的資料轉換和分析任務。
    *   **服務**: `spark-master` (Spark 集群主節點), `spark-worker` (Spark 集群工作節點)。

## 先決條件

在啟動此資料管道之前，請確保您的系統已安裝以下軟體：

*   **Docker**: [安裝指南](https://docs.docker.com/get-docker/)
*   **Docker Compose**: 通常隨 Docker Desktop 一起安裝。如果沒有，請參考 [安裝指南](https://docs.docker.com/compose/install/)

## 設定與啟動

請按照以下步驟啟動資料管道服務：

1.  **複製專案**:
    ```bash
    git clone <你的專案 Git URL>
    cd teeth_mvp/data_pipeline
    ```
    (請將 `<你的專案 Git URL>` 替換為你的實際 Git 倉庫 URL)

2.  **啟動服務**:
    在 `data_pipeline` 目錄下，執行以下命令來構建並啟動所有服務：
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: 確保所有服務的鏡像都是最新構建的。
    *   `-d`: 在後台運行容器。

    首次啟動時，`airflow-init` 容器會執行資料庫遷移和建立管理員使用者。這個容器在完成任務後會自動退出，這是正常行為。

## 使用方式

服務啟動後，您可以透過以下網址訪問各個介面：

*   **Airflow UI**:
    *   網址: `http://localhost:8080`
    *   預設登入資訊:
        *   使用者名稱: `admin`
        *   密碼: `admin`

*   **Spark Master UI**:
    *   網址: `http://localhost:8081`

### 放置您的 DAGs

您可以將您的 Airflow DAGs (Directed Acyclic Graphs) 檔案放置在 `data_pipeline/dags` 目錄中。Airflow 容器會自動掛載此目錄，並載入其中的 DAGs。

## 故障排除

*   **`data_pipeline-airflow-init-1` 容器 `Exited (0)`**: 這是預期行為。此容器的任務是執行一次性初始化，完成後會自動退出。
*   **服務無法啟動**: 檢查 Docker 和 Docker Compose 是否正確安裝並運行。您可以使用 `docker ps -a` 查看所有容器的狀態，並使用 `docker logs <容器ID或名稱>` 查看特定容器的日誌以獲取更多資訊。
*   **Airflow 登入問題**: 確保您使用的是預設的 `admin/admin` 憑證。如果需要，您可以透過 `docker-compose exec airflow-webserver airflow users create ...` 命令來建立新的使用者。
