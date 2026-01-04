import { S3Client, PutObjectCommand, GetObjectCommand, DeleteObjectCommand, HeadObjectCommand } from '@aws-sdk/client-s3'
import { config } from './config.js'

let s3Client: S3Client | null = null

export function initBlobStore(): void {
  s3Client = new S3Client({
    endpoint: config.s3.endpoint,
    region: config.s3.region,
    credentials: {
      accessKeyId: config.s3.accessKey,
      secretAccessKey: config.s3.secretKey,
    },
    forcePathStyle: true,
  })
}

function getClient(): S3Client {
  if (!s3Client) throw new Error('Blob store not initialized')
  return s3Client
}

function blobKey(blobId: string): string {
  const prefix = blobId.slice(0, 2) || '00'
  return `${prefix}/${blobId}.json`
}

export async function saveBlob(blobId: string, data: unknown): Promise<string> {
  const client = getClient()
  const key = blobKey(blobId)
  const body = JSON.stringify(data)

  await client.send(new PutObjectCommand({
    Bucket: config.s3.bucket,
    Key: key,
    Body: body,
    ContentType: 'application/json',
  }))

  return key
}

export async function loadBlob<T>(blobId: string): Promise<T | null> {
  const client = getClient()
  const key = blobKey(blobId)

  try {
    const response = await client.send(new GetObjectCommand({
      Bucket: config.s3.bucket,
      Key: key,
    }))
    const body = await response.Body?.transformToString()
    if (body) return JSON.parse(body) as T
    return null
  } catch {
    return null
  }
}

export async function deleteBlob(blobId: string): Promise<boolean> {
  const client = getClient()
  const key = blobKey(blobId)

  try {
    await client.send(new DeleteObjectCommand({
      Bucket: config.s3.bucket,
      Key: key,
    }))
    return true
  } catch {
    return false
  }
}

export async function blobExists(blobId: string): Promise<boolean> {
  const client = getClient()
  const key = blobKey(blobId)

  try {
    await client.send(new HeadObjectCommand({
      Bucket: config.s3.bucket,
      Key: key,
    }))
    return true
  } catch {
    return false
  }
}

// Candidate Set helpers
export async function saveCandidateSet(stepId: string, candidateSet: Record<string, unknown>): Promise<string> {
  const blobId = `cs_${stepId}`
  return saveBlob(blobId, candidateSet)
}

export async function loadCandidateSet(stepId: string): Promise<Record<string, unknown> | null> {
  const blobId = `cs_${stepId}`
  return loadBlob(blobId)
}

// Artifact helpers
export async function saveArtifact(artifactId: string, content: unknown): Promise<string> {
  const blobId = `art_${artifactId}`
  return saveBlob(blobId, content)
}

export async function loadArtifact(artifactId: string): Promise<unknown | null> {
  const blobId = `art_${artifactId}`
  return loadBlob(blobId)
}

