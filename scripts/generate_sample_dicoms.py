#!/usr/bin/env python3
"""
Generate compliant DICOM (.dcm) sample files from example X-ray images
to allow immediate testing without downloading external gigabyte datasets.
"""

from pathlib import Path
import datetime
import numpy as np
from PIL import Image
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid


def convert_image_to_dicom(
    source_img_path: Path,
    target_dcm_path: Path,
    patient_id: str,
    patient_name: str,
    study_description: str,
):
    print(f"Converting {source_img_path.name} -> {target_dcm_path.name}...")
    img = Image.open(source_img_path).convert("L")
    np_img = np.array(img, dtype=np.uint8)

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(str(target_dcm_path), {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.is_little_endian = True
    ds.is_implicit_VR = False

    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()

    ds.PatientID = patient_id
    ds.PatientName = patient_name
    ds.PatientBirthDate = "19800512"
    ds.PatientSex = "M"

    now = datetime.datetime.now()
    ds.StudyDate = now.strftime("%Y%m%d")
    ds.StudyTime = now.strftime("%H%M%S")
    ds.Modality = "CR"
    ds.BodyPartExamined = "CHEST"
    ds.PatientPosition = "PA"
    ds.StudyDescription = study_description
    ds.InstitutionName = "Hospital Geral de Radiologia"

    ds.Rows, ds.Columns = np_img.shape
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.SamplesPerPixel = 1
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.WindowCenter = "128"
    ds.WindowWidth = "256"
    ds.RescaleIntercept = "0"
    ds.RescaleSlope = "1"

    ds.PixelData = np_img.tobytes()
    ds.save_as(str(target_dcm_path), write_like_original=False)
    print(f"Created: {target_dcm_path} ({target_dcm_path.stat().st_size} bytes)")


def main():
    root = Path(__file__).resolve().parent.parent
    examples_dir = root / "examples"
    output_dir = examples_dir / "dicom"
    output_dir.mkdir(parents=True, exist_ok=True)

    samples = [
        (
            examples_dir / "normal_1.jpeg",
            output_dir / "sample_normal.dcm",
            "PAT_NORMAL_01",
            "DOE^JOHN",
            "Radiografia de Torax PA - Rotina Normal",
        ),
        (
            examples_dir / "covid_1.jpg",
            output_dir / "sample_covid.dcm",
            "PAT_COVID_02",
            "SILVA^MARIA",
            "Radiografia de Torax PA - Suspeita Covid-19",
        ),
        (
            examples_dir / "bacterial_pneumonia_1.jpeg",
            output_dir / "sample_pneumonia_bacteriana.dcm",
            "PAT_PNEUMO_BAC_03",
            "SANTOS^CARLOS",
            "Radiografia de Torax PA - Pneumonia Bacteriana Lobar",
        ),
        (
            examples_dir / "viral_pneumonia_1.jpeg",
            output_dir / "sample_pneumonia_viral.dcm",
            "PAT_PNEUMO_VIR_04",
            "OLIVEIRA^ANA",
            "Radiografia de Torax PA - Pneumonia Viral Intersticial",
        ),
    ]

    for src, dst, pid, pname, desc in samples:
        if src.exists():
            convert_image_to_dicom(src, dst, pid, pname, desc)
        else:
            print(f"Skipping {src.name} (not found)")

    print("\nAll sample DICOM files generated successfully in examples/dicom/")


if __name__ == "__main__":
    main()
