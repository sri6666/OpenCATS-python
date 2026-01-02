"""
File Upload Handler
Supports local storage and AWS S3
"""
import os
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app


ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'rtf', 'txt', 'odt', 'jpg', 'jpeg', 'png', 'gif'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, site_id, category='general'):
    """
    Save uploaded file to storage

    Args:
        file: FileStorage object
        site_id: Site ID for multi-tenant isolation
        category: Upload category (resumes, attachments, images)

    Returns:
        tuple: (filename, file_path, file_size)
    """
    if current_app.config.get('USE_S3'):
        return save_to_s3(file, site_id, category)
    else:
        return save_to_local(file, site_id, category)


def save_to_local(file, site_id, category):
    """Save file to local filesystem"""
    # Generate unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    original_filename = secure_filename(file.filename)
    name, ext = os.path.splitext(original_filename)

    # Create unique filename with hash
    file_hash = hashlib.md5(f"{site_id}{timestamp}{name}".encode()).hexdigest()[:8]
    filename = f"{name}_{file_hash}{ext}"

    # Create directory structure: uploads/site_ID/category/
    upload_dir = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        str(site_id),
        category
    )
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    # Get file size
    file_size = os.path.getsize(file_path)

    return filename, file_path, file_size


def save_to_s3(file, site_id, category):
    """Save file to AWS S3"""
    import boto3
    from botocore.exceptions import ClientError

    s3_client = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_S3_REGION']
    )

    # Generate unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    original_filename = secure_filename(file.filename)
    name, ext = os.path.splitext(original_filename)

    file_hash = hashlib.md5(f"{site_id}{timestamp}{name}".encode()).hexdigest()[:8]
    filename = f"{name}_{file_hash}{ext}"

    # S3 key: site_id/category/filename
    s3_key = f"{site_id}/{category}/{filename}"

    try:
        # Upload to S3
        s3_client.upload_fileobj(
            file,
            current_app.config['AWS_S3_BUCKET'],
            s3_key,
            ExtraArgs={
                'ContentType': file.content_type,
                'ServerSideEncryption': 'AES256'
            }
        )

        # Get file size
        response = s3_client.head_object(
            Bucket=current_app.config['AWS_S3_BUCKET'],
            Key=s3_key
        )
        file_size = response['ContentLength']

        # S3 URL
        file_path = f"s3://{current_app.config['AWS_S3_BUCKET']}/{s3_key}"

        return filename, file_path, file_size

    except ClientError as e:
        raise Exception(f"S3 upload failed: {str(e)}")


def delete_file(file_path, storage_type='local'):
    """Delete file from storage"""
    if storage_type == 's3':
        delete_from_s3(file_path)
    else:
        delete_from_local(file_path)


def delete_from_local(file_path):
    """Delete file from local filesystem"""
    if os.path.exists(file_path):
        os.remove(file_path)


def delete_from_s3(s3_url):
    """Delete file from S3"""
    import boto3

    # Parse S3 URL: s3://bucket/key
    if not s3_url.startswith('s3://'):
        return

    parts = s3_url[5:].split('/', 1)
    bucket = parts[0]
    key = parts[1]

    s3_client = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_S3_REGION']
    )

    s3_client.delete_object(Bucket=bucket, Key=key)


def get_file_url(attachment):
    """Get public URL for attachment"""
    if attachment.storage_type == 's3':
        return get_s3_url(attachment.storage_path)
    else:
        # For local files, return download URL
        from flask import url_for
        return url_for('attachments.download', id=attachment.attachment_id)


def get_s3_url(s3_url, expiration=3600):
    """Generate presigned URL for S3 object"""
    import boto3

    if not s3_url.startswith('s3://'):
        return s3_url

    parts = s3_url[5:].split('/', 1)
    bucket = parts[0]
    key = parts[1]

    s3_client = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_S3_REGION']
    )

    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=expiration
    )

    return url
