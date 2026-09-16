# Group A deployment paths

The downloadable frontend works as a static site. FastAPI, PostgreSQL, Spark and AWS are separate runnable components. No AWS resources are provisioned by opening the website.

## Free presentation website on Vercel

Import this repository. Framework: Other. Build command: `npm run build`. Output: `dist`. The committed build also works with an empty build command. No server or API key is required for this static configuration. Keep `dist/config.js` API base empty. Current forecasts and location searches call Open-Meteo directly; history uses the packaged daily dataset. Vercel Hobby is intended for personal/non-commercial use; check current plan terms before deployment.

## FastAPI on the 8 GB laptop

Create a Python 3.12 environment. Install `backend/requirements.txt`. Run `uvicorn backend.main:app --host 127.0.0.1 --port 8001`. API documentation: http://127.0.0.1:8001/docs. With no DATABASE_URL, the API serves packaged historical data. Set `dist/config.js` to `{ apiBase: 'http://localhost:8001' }` while serving the frontend at localhost:8000. Use an HTTPS backend origin for an HTTPS hosted frontend. All dashboard history, EDA and global requests use the configured backend.

## Local PostgreSQL

Copy `.env.example` to `.env`, set a strong URL-safe password, then run `docker compose up --build -d`. Install `pipeline/requirements-cloud.txt`. Export DATABASE_URL from your local configuration and run `python pipeline/publish_cloud.py --postgres`. This loads cleaned analytical rows using an idempotent upsert. The API's `/api/history/{location_id}` then queries PostgreSQL. Docker is optional for the static demonstration; avoid running Spark and Docker simultaneously on an 8 GB laptop.

## Parquet and Spark

Run `python pipeline/export_parquet.py`. Source hourly values, source-model labels and missing values are preserved. Local files are partitioned by district/year to avoid nearly 100,000 tiny files. Spark's processed daily output is partitioned by district/date. Set the notebook raw_date_partitions widget to true for the proposal's exact raw district/date partitioning; this creates many small files for point data. CSV is provided for inspection and course submission; Parquet supports typed, compressed columnar scans; JSON is limited to API responses and compact dashboard results.

Import `pipeline/databricks_spark.py` as a Python notebook in Databricks. Create a Unity Catalog volume and upload the raw-hourly and raw-daily Parquet directories. Set the three notebook path widgets. Run every cell, capture the job output and execution times. The notebook cleans invalid values, removes duplicate keys, requires complete days, joins discharge, computes accumulation windows and approximate monthly percentile anomalies, and writes seasonal/daily results. It does not fit a forecasting model. Download the processed daily Parquet output and use `python pipeline/publish_cloud.py --postgres --spark-daily /path/to/downloaded/daily` to load the Spark results into PostgreSQL. The optional JDBC example requires a workspace that can reach the database.

Databricks Free Edition has restricted outbound network access and usage quotas. Uploading into a volume is the portable free route. Do not assume a free workspace can connect directly to a private RDS endpoint or arbitrary S3 bucket. A configured student/paid workspace with storage credentials and network access is needed for that direct cloud path.

## Optional local Spark verification

With Java 17 and `pyspark==3.5.6`, run `python pipeline/run_spark_local.py` after Parquet export. It executes the same notebook with two local worker threads and 2 GB driver memory, then checks row counts and unique daily keys. It uses compact district partitions locally. `dist/data/spark-validation.json` records the measured run; it is not a Databricks result.

## AWS S3 and RDS

AWS is optional for the free frontend but required to demonstrate the proposal's exact cloud infrastructure. Charges may apply even with student credits. Terraform config uses an existing VPC, two private subnets and the backend's security group. It creates a private encrypted S3 bucket and encrypted private RDS PostgreSQL instance. It does not create a publicly accessible database or deploy the API compute host.

Install Terraform and AWS CLI; authenticate to your own account. Copy `infra/terraform.tfvars.example` to `infra/terraform.tfvars`, fill your resource IDs and a unique bucket name; supply the database password through TF_VAR_db_password. Run `terraform init`, `terraform validate`, and `terraform plan` from infra. Review the concrete plan and costs before `terraform apply`. Terraform state contains secrets and must be protected; it is excluded from Git.

Run the FastAPI container on a host in the permitted VPC security group, behind HTTPS. Use RDS credentials through a secrets manager/environment, with `sslmode=require` in DATABASE_URL. Set FRONTEND_ORIGINS to the exact deployed frontend origin. Set S3_BUCKET and AWS_REGION and run `python pipeline/publish_cloud.py --s3 --postgres` from a network that can reach RDS. Standard AWS credentials/roles are used; none are bundled. S3/RDS/Databricks cloud execution has to be completed in the team's own accounts and recorded honestly in the report.

## Threshold correction

Open-Meteo Flood API does not expose 2-, 5- or 20-year return-period threshold variables. Its p25/p75 fields describe forecast ensemble spread. The implementation uses explicitly labelled monthly historical percentile screening. It neither calls these return periods nor claims calibrated flood probabilities. If the course requires return periods, obtain a verified threshold dataset and revise the declared data-source scope; do not invent API fields.

Sources: https://open-meteo.com/en/docs/flood-api · https://docs.databricks.com/aws/en/getting-started/free-edition-limitations · https://vercel.com/docs/plans/hobby
