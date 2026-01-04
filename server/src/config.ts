import dotenv from 'dotenv'

dotenv.config()

export const config = {
  postgres: {
    host: process.env.XRAY_POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.XRAY_POSTGRES_PORT || '5432'),
    user: process.env.XRAY_POSTGRES_USER || 'xray',
    password: process.env.XRAY_POSTGRES_PASSWORD || 'xray_secret',
    database: process.env.XRAY_POSTGRES_DB || 'xray',
  },
  redis: {
    host: process.env.XRAY_REDIS_HOST || 'localhost',
    port: parseInt(process.env.XRAY_REDIS_PORT || '6379'),
    db: parseInt(process.env.XRAY_REDIS_DB || '0'),
  },
  s3: {
    endpoint: process.env.XRAY_S3_ENDPOINT || 'http://localhost:9000',
    accessKey: process.env.XRAY_S3_ACCESS_KEY || 'minioadmin',
    secretKey: process.env.XRAY_S3_SECRET_KEY || 'minioadmin',
    bucket: process.env.XRAY_S3_BUCKET || 'xray-blobs',
    region: process.env.XRAY_S3_REGION || 'us-east-1',
  },
  port: parseInt(process.env.PORT || '8000'),
}

