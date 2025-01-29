# How to Run or Activate the Environment

To set up and activate the environment for this project, follow these steps:

1. **Clone the Repository**
    ```sh
    git clone https://github.com/yourusername/your-repo.git
    cd your-repo
    ```

2. **Create a Virtual Environment**
    ```sh
    python3 -m venv env
    ```

3. **Activate the Virtual Environment**

    - On macOS and Linux:
      ```sh
      source env/bin/activate
      ```
    - On Windows:
      ```sh
      .\env\Scripts\activate
      ```
      
4. **Install Dependencies**
    ```sh
    poetry install
    ```

5. **Run the Application**
    ```sh
    poetry run uvicorn app.main:app --reload
    ```

docker build -t hcc-extractor .