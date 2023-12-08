# API 說明文件

## 設置

在進行測試之前，請確保：

- 已安裝 Postman。

## Service API 端點說明

Service API 提供以下端點：

1. 創建文檔：`POST /create`
2. 讀取所有[collection_name]：`GET /read`
3. 讀取特定專案：`GET /read_project/<name>`
4. 讀取特定社員：`GET /read_member/<email>`
5. 更新文檔：`PUT /update/<collection>/<doc_id>`
6. 刪除文檔：`DELETE /delete/<collection>/<doc_id>`

## 測試指南

### 1. 創建文檔

- 方法：`POST`
- URL：`https://testforgdsc.pythonanywhere.com/create`
- 主體：JSON (application/json)
  - 示例：

    ```json
    {
      "collection": "notes",
      "data": {
        "name": "Sample Note",
        "date": "2023/11/25",
        "link": "http://gdsc.com/note"
      }
    }
    ```

### 2. 讀取所有[collection_name]

- 方法：`GET`
- URL：`https://testforgdsc.pythonanywhere.com/read?collection=collection_name`

### 3. 讀取特定專案

- 方法：`GET`
- URL：`https://testforgdsc.pythonanywhere.com/read_project/project_name`

### 4. 讀取特定社員

- 方法：`GET`
- URL：`https://testforgdsc.pythonanywhere.com/read_member/email_address`

### 5. 更新文檔

- 方法：`PUT`
- URL：`https://testforgdsc.pythonanywhere.com/update/collection_name/document_id`
- 主體：JSON (application/json)
  - 示例：

    ```json
    {
      "key_to_update": "new_value"
    }
    ```

### 6. 刪除文檔

- 方法：`DELETE`
- URL：`https://testforgdsc.pythonanywhere.com/delete/collection_name/document_id`

## 使用 Postman 測試

1. 打開 Postman。
2. 根據端點選擇方法（GET, POST, PUT, DELETE）。
3. 輸入 URL。
4. 對於 `POST` 和 `PUT` 請求，選擇 `Body`，然後選擇 `raw`，並選擇 `JSON`。
5. 根據需要輸入請求主體。
6. 點擊 `Send` 發送請求。
7. 查看響應和狀態碼以進行驗證。
