from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pathlib import Path
from uuid import uuid4
from PIL import Image as PILImage
from sqlalchemy.orm import Session
import shutil

from .database import SessionLocal
from .models import Patient, Image as ImageRecord
from .services import assess_image_quality

router = APIRouter()


# Folder where uploaded images are stored
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    age: int | None = Form(None),
    gender: str | None = Form(None)
):

    # Check file extension
    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG and PNG images are allowed."
        )

    # Generate unique IDs
    patient_id = f"PAT_{uuid4().hex[:8]}"
    image_id = f"IMG_{uuid4().hex[:8]}"

    saved_filename = f"{image_id}{extension}"
    file_path = UPLOAD_DIR / saved_filename

    # Save uploaded image
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Verify that uploaded file is a valid image
    try:
        with PILImage.open(file_path) as image:
            image.verify()

    except Exception:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image."
        )

    # Database connection
    db: Session = SessionLocal()

    try:

        # Create patient
        patient = Patient(
            patient_id=patient_id,
            age=age,
            gender=gender
        )

        db.add(patient)

        # Create image record
        image_record = ImageRecord(
            image_id=image_id,
            patient_id=patient_id,
            filename=saved_filename,
            quality_status="pending"
        )

        db.add(image_record)

        db.commit()

    except Exception as e:

        db.rollback()

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    finally:
        db.close()

    return {
        "status": "uploaded",
        "message": "Retinal image uploaded successfully.",
        "patient_id": patient_id,
        "image_id": image_id,
        "filename": saved_filename
    }

@router.post("/quality/{image_id}")
def check_image_quality(image_id: str):

    db: Session = SessionLocal()

    try:

        # Find image in database
        image_record = (
            db.query(ImageRecord)
            .filter(ImageRecord.image_id == image_id)
            .first()
        )

        if image_record is None:
            raise HTTPException(
                status_code=404,
                detail="Image ID not found."
            )

        # Build image path
        image_path = Path("uploads") / image_record.filename

        # Run quality assessment
        quality_result = assess_image_quality(str(image_path))

        # Update database
        image_record.quality_status = quality_result["status"]

        db.commit()

        return {
            "image_id": image_id,
            "quality": quality_result
        }

    except HTTPException:
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Quality assessment error: {str(e)}"
        )

    finally:
        db.close()