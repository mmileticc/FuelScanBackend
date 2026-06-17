# FuelScan Backend ⚙️🚀

The lightweight, asynchronous backend API powering the **FuelScan** ecosystem. Built with **FastAPI**, this service handles token validation and coordinates the receipt parsing pipeline.

> ⚠️ **Project Status:** This backend is currently a minimalist MVP. The core logic is intentionally kept simple and unified to ensure fast execution and straightforward prototyping.

---

### ⚡ Key Features

*   **Asynchronous Processing:** Utilizes FastAPI's native `async/await` and `httpx` for efficient, non-blocking requests.
*   **Token Validation:** Implements a dependency middleware (`get_current_user`) to validate incoming user requests against Supabase Auth endpoints.
*   **Parsing Integration:** Exposes a clean POST endpoint (`/parse-receipt`) that triggers the internal parsing engine to extract structured data from fuel receipts.
*   **Docker Ready:** Includes a `Dockerfile` for quick containerization and deployment.

---

### 🛠️ Tech Stack

*   **Framework:** FastAPI (Python)
*   **HTTP Client:** Httpx (Asynchronous requests)
*   **Server:** Uvicorn
*   **Containerization:** Docker

---

### 📂 Repository Structure

*   `main.py` – Contains the FastAPI app configuration, security dependency, and core API endpoints.
*   `parser.py` – Houses the logic for processing and extracting data from receipts.
*   `Dockerfile` – Blueprint for containerizing the application.
