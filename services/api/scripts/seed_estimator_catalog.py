#!/usr/bin/env python3
"""Seed work codes and material catalog for the estimator module."""

import logging
import os
import sys
from datetime import datetime, UTC
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


# ============================================================
# Standard Work Codes - Eagle Sign Labor Categories
# ============================================================

WORK_CODES = [
    # Fabrication
    ("FAB-01", "Layout and Template", "fabrication", 65.00, 2.0),
    ("FAB-02", "CNC Programming", "fabrication", 75.00, 1.5),
    ("FAB-03", "Aluminum Fabrication", "fabrication", 65.00, 4.0),
    ("FAB-04", "Steel Fabrication", "fabrication", 70.00, 6.0),
    ("FAB-05", "Channel Letter Assembly", "fabrication", 60.00, 0.5),  # Per letter
    ("FAB-06", "Cabinet Assembly", "fabrication", 65.00, 8.0),
    ("FAB-07", "Monument Structure", "fabrication", 70.00, 12.0),
    ("FAB-08", "Pole Structure Fabrication", "fabrication", 75.00, 16.0),
    ("FAB-09", "Pylon Structure", "fabrication", 80.00, 24.0),
    ("FAB-10", "Finishing/Paint Prep", "fabrication", 55.00, 4.0),

    # Engineering
    ("ENG-01", "Structural Calculations", "engineering", 125.00, 4.0),
    ("ENG-02", "Foundation Design", "engineering", 125.00, 2.0),
    ("ENG-03", "Wind Load Analysis", "engineering", 125.00, 2.0),
    ("ENG-04", "PE Stamp Review", "engineering", 150.00, 1.0),
    ("ENG-05", "Shop Drawings", "engineering", 85.00, 4.0),
    ("ENG-06", "Permit Drawings", "engineering", 85.00, 3.0),
    ("ENG-07", "As-Built Documentation", "engineering", 75.00, 2.0),

    # Installation
    ("INS-01", "Site Survey", "installation", 75.00, 2.0),
    ("INS-02", "Excavation - Manual", "installation", 65.00, 4.0),
    ("INS-03", "Excavation - Mechanical", "installation", 85.00, 2.0),
    ("INS-04", "Concrete Pour", "installation", 70.00, 3.0),
    ("INS-05", "Anchor Bolt Setting", "installation", 70.00, 1.5),
    ("INS-06", "Sign Installation - Ground", "installation", 75.00, 4.0),
    ("INS-07", "Sign Installation - Wall", "installation", 80.00, 3.0),
    ("INS-08", "Sign Installation - Roof", "installation", 90.00, 6.0),
    ("INS-09", "Crane Work", "installation", 125.00, 4.0),
    ("INS-10", "Bucket Truck Work", "installation", 95.00, 3.0),
    ("INS-11", "Traffic Control", "installation", 55.00, 8.0),
    ("INS-12", "Final Inspection Prep", "installation", 65.00, 1.0),

    # Electrical
    ("ELE-01", "Electrical Layout", "electrical", 85.00, 2.0),
    ("ELE-02", "LED Module Installation", "electrical", 75.00, 2.0),
    ("ELE-03", "Power Supply Install", "electrical", 75.00, 1.0),
    ("ELE-04", "Transformer Installation", "electrical", 85.00, 2.0),
    ("ELE-05", "Conduit Run", "electrical", 70.00, 3.0),
    ("ELE-06", "Wire Pull", "electrical", 65.00, 2.0),
    ("ELE-07", "Connection to Service", "electrical", 90.00, 2.0),
    ("ELE-08", "Lighting Test/Commission", "electrical", 75.00, 1.0),

    # Graphics
    ("GFX-01", "Vinyl Production", "graphics", 55.00, 2.0),
    ("GFX-02", "Vinyl Application", "graphics", 60.00, 3.0),
    ("GFX-03", "Digital Print", "graphics", 65.00, 2.0),
    ("GFX-04", "Face Application", "graphics", 60.00, 2.0),
    ("GFX-05", "Paint/Finish", "graphics", 70.00, 4.0),

    # Project Management
    ("PM-01", "Project Coordination", "project_management", 95.00, 4.0),
    ("PM-02", "Permit Coordination", "project_management", 85.00, 3.0),
    ("PM-03", "Customer Meetings", "project_management", 95.00, 2.0),
    ("PM-04", "Subcontractor Coordination", "project_management", 85.00, 2.0),
    ("PM-05", "Shipping/Logistics", "project_management", 65.00, 2.0),

    # Repair/Service
    ("SVC-01", "Service Call - Standard", "service", 85.00, 2.0),
    ("SVC-02", "Service Call - Emergency", "service", 125.00, 2.0),
    ("SVC-03", "Lamp/LED Replacement", "service", 75.00, 1.0),
    ("SVC-04", "Face Replacement", "service", 70.00, 2.0),
    ("SVC-05", "Ballast/Driver Replacement", "service", 80.00, 1.5),
    ("SVC-06", "Structural Repair", "service", 85.00, 4.0),
]


# ============================================================
# Material Catalog - Standard Sign Industry Materials
# ============================================================

MATERIALS = [
    # Aluminum Sheet
    ("AL-4X8-040", "Aluminum Sheet 4x8 .040", "aluminum", "sheet", 85.00, "Metal Supermarkets", "4x8-040-AL", 3),
    ("AL-4X8-063", "Aluminum Sheet 4x8 .063", "aluminum", "sheet", 125.00, "Metal Supermarkets", "4x8-063-AL", 3),
    ("AL-4X8-080", "Aluminum Sheet 4x8 .080", "aluminum", "sheet", 165.00, "Metal Supermarkets", "4x8-080-AL", 3),
    ("AL-4X8-125", "Aluminum Sheet 4x8 .125", "aluminum", "sheet", 245.00, "Metal Supermarkets", "4x8-125-AL", 5),
    ("AL-4X10-063", "Aluminum Sheet 4x10 .063", "aluminum", "sheet", 155.00, "Metal Supermarkets", "4x10-063-AL", 3),

    # Aluminum Extrusions
    ("AL-EXT-2X2", "Aluminum Tube 2x2x.125", "aluminum", "linear_ft", 4.50, "Metal Supermarkets", "2X2-125-AL", 5),
    ("AL-EXT-3X3", "Aluminum Tube 3x3x.125", "aluminum", "linear_ft", 6.75, "Metal Supermarkets", "3X3-125-AL", 5),
    ("AL-EXT-4X4", "Aluminum Tube 4x4x.188", "aluminum", "linear_ft", 12.50, "Metal Supermarkets", "4X4-188-AL", 7),
    ("AL-ANG-2X2", "Aluminum Angle 2x2x.125", "aluminum", "linear_ft", 3.25, "Metal Supermarkets", "ANG-2X2-AL", 5),
    ("AL-CHAN-4", "Aluminum Channel 4\"", "aluminum", "linear_ft", 8.50, "Metal Supermarkets", "CHAN-4-AL", 5),

    # Steel
    ("STL-HSS-4X4", "Steel HSS 4x4x.25", "steel", "linear_ft", 18.50, "Metal Supermarkets", "HSS-4X4-25", 7),
    ("STL-HSS-6X6", "Steel HSS 6x6x.25", "steel", "linear_ft", 28.75, "Metal Supermarkets", "HSS-6X6-25", 7),
    ("STL-HSS-8X8", "Steel HSS 8x8x.375", "steel", "linear_ft", 52.00, "Metal Supermarkets", "HSS-8X8-375", 10),
    ("STL-PIPE-4", "Steel Pipe 4\" Sch 40", "steel", "linear_ft", 15.50, "Metal Supermarkets", "PIPE-4-SCH40", 7),
    ("STL-PIPE-6", "Steel Pipe 6\" Sch 40", "steel", "linear_ft", 28.00, "Metal Supermarkets", "PIPE-6-SCH40", 7),
    ("STL-PIPE-8", "Steel Pipe 8\" Sch 40", "steel", "linear_ft", 45.00, "Metal Supermarkets", "PIPE-8-SCH40", 10),
    ("STL-PL-0.25", "Steel Plate 1/4\"", "steel", "sq_ft", 12.50, "Metal Supermarkets", "PL-25", 5),
    ("STL-PL-0.375", "Steel Plate 3/8\"", "steel", "sq_ft", 18.75, "Metal Supermarkets", "PL-375", 5),
    ("STL-PL-0.5", "Steel Plate 1/2\"", "steel", "sq_ft", 25.00, "Metal Supermarkets", "PL-50", 7),

    # Acrylic/Polycarbonate
    ("ACR-3MM-WHT", "Acrylic 3mm White", "acrylic", "sheet", 125.00, "Piedmont Plastics", "ACR-3-W", 5),
    ("ACR-3MM-CLR", "Acrylic 3mm Clear", "acrylic", "sheet", 115.00, "Piedmont Plastics", "ACR-3-C", 5),
    ("ACR-6MM-WHT", "Acrylic 6mm White", "acrylic", "sheet", 195.00, "Piedmont Plastics", "ACR-6-W", 5),
    ("PC-3MM-WHT", "Polycarbonate 3mm White", "acrylic", "sheet", 165.00, "Piedmont Plastics", "PC-3-W", 5),
    ("PC-3MM-CLR", "Polycarbonate 3mm Clear", "acrylic", "sheet", 155.00, "Piedmont Plastics", "PC-3-C", 5),
    ("LEXAN-4X8", "Lexan 4x8 .118\"", "acrylic", "sheet", 225.00, "Piedmont Plastics", "LEX-118", 7),

    # LED Modules
    ("LED-MOD-WHT", "LED Module White 3-LED", "electrical", "each", 3.25, "SloanLED", "WH-3LED", 14),
    ("LED-MOD-RED", "LED Module Red 3-LED", "electrical", "each", 3.50, "SloanLED", "RD-3LED", 14),
    ("LED-MOD-BLU", "LED Module Blue 3-LED", "electrical", "each", 3.75, "SloanLED", "BL-3LED", 14),
    ("LED-MOD-GRN", "LED Module Green 3-LED", "electrical", "each", 3.50, "SloanLED", "GR-3LED", 14),
    ("LED-PS-100W", "LED Power Supply 100W", "electrical", "each", 45.00, "SloanLED", "PS-100", 14),
    ("LED-PS-200W", "LED Power Supply 200W", "electrical", "each", 75.00, "SloanLED", "PS-200", 14),
    ("LED-PS-350W", "LED Power Supply 350W", "electrical", "each", 125.00, "SloanLED", "PS-350", 14),

    # Vinyl
    ("VNL-3M-WHT", "3M Vinyl White", "vinyl", "sq_ft", 1.85, "FELLERS", "3M-180C-10", 3),
    ("VNL-3M-BLK", "3M Vinyl Black", "vinyl", "sq_ft", 1.85, "FELLERS", "3M-180C-12", 3),
    ("VNL-3M-RED", "3M Vinyl Red", "vinyl", "sq_ft", 2.10, "FELLERS", "3M-180C-53", 3),
    ("VNL-3M-BLU", "3M Vinyl Blue", "vinyl", "sq_ft", 2.10, "FELLERS", "3M-180C-47", 3),
    ("VNL-REFL", "Reflective Vinyl", "vinyl", "sq_ft", 4.50, "FELLERS", "3M-680-10", 5),
    ("VNL-TRANS-APP", "Vinyl Transfer Application", "vinyl", "sq_ft", 0.35, "FELLERS", "R-TAPE-4000", 3),
    ("VNL-LAM", "Vinyl Laminate", "vinyl", "sq_ft", 0.85, "FELLERS", "3M-8518", 3),

    # Fasteners
    ("FST-AB-0.5X12", "Anchor Bolt 1/2x12\"", "fasteners", "each", 4.25, "Fastenal", "AB-12-12", 3),
    ("FST-AB-0.75X18", "Anchor Bolt 3/4x18\"", "fasteners", "each", 8.50, "Fastenal", "AB-34-18", 3),
    ("FST-AB-1X24", "Anchor Bolt 1\"x24\"", "fasteners", "each", 15.00, "Fastenal", "AB-1-24", 5),
    ("FST-LAG-0.25X3", "Lag Bolt 1/4x3\"", "fasteners", "each", 0.45, "Fastenal", "LAG-14-3", 3),
    ("FST-LAG-0.375X4", "Lag Bolt 3/8x4\"", "fasteners", "each", 0.85, "Fastenal", "LAG-38-4", 3),
    ("FST-SS-TEKS", "SS Tek Screw #10x1\"", "fasteners", "each", 0.18, "Fastenal", "TEK-10-1-SS", 3),
    ("FST-RIVET-AL", "Aluminum Rivet 3/16\"", "fasteners", "each", 0.08, "Fastenal", "RIV-316-AL", 3),

    # Concrete
    ("CON-5000", "Concrete 5000 PSI", "concrete", "cubic_yard", 165.00, "Ready Mix USA", "RM-5000", 1),
    ("CON-REBAR-4", "Rebar #4", "concrete", "linear_ft", 0.85, "Metal Supermarkets", "REBAR-4", 5),
    ("CON-REBAR-5", "Rebar #5", "concrete", "linear_ft", 1.25, "Metal Supermarkets", "REBAR-5", 5),
    ("CON-MESH-6X6", "Wire Mesh 6x6 W1.4", "concrete", "sheet", 45.00, "Metal Supermarkets", "MESH-6X6", 5),
    ("CON-FORM-TUBE", "Sonotube 12\"", "concrete", "linear_ft", 8.50, "Home Depot Pro", "SONO-12", 3),

    # Paint/Finish
    ("PNT-PRIMER", "Zinc Primer", "paint", "gallon", 55.00, "Sherwin Williams", "Z-PRIME", 3),
    ("PNT-ENAMEL", "Industrial Enamel", "paint", "gallon", 75.00, "Sherwin Williams", "IND-ENAM", 3),
    ("PNT-POWDER", "Powder Coat - Standard", "paint", "lb", 12.50, "Tiger Drylac", "PC-STD", 5),
    ("PNT-POWDER-MT", "Powder Coat - Metallic", "paint", "lb", 18.50, "Tiger Drylac", "PC-MET", 7),
    ("GAL-HDG", "Hot Dip Galvanizing", "paint", "lb", 1.85, "Valmont", "HDG-STD", 10),

    # Electrical
    ("ELE-WIRE-12", "Wire 12 AWG THHN", "electrical", "linear_ft", 0.35, "Graybar", "THHN-12", 3),
    ("ELE-WIRE-10", "Wire 10 AWG THHN", "electrical", "linear_ft", 0.55, "Graybar", "THHN-10", 3),
    ("ELE-WIRE-8", "Wire 8 AWG THHN", "electrical", "linear_ft", 0.85, "Graybar", "THHN-8", 3),
    ("ELE-COND-0.5", "EMT Conduit 1/2\"", "electrical", "linear_ft", 1.25, "Graybar", "EMT-12", 3),
    ("ELE-COND-0.75", "EMT Conduit 3/4\"", "electrical", "linear_ft", 1.65, "Graybar", "EMT-34", 3),
    ("ELE-COND-1", "EMT Conduit 1\"", "electrical", "linear_ft", 2.15, "Graybar", "EMT-1", 3),
    ("ELE-JB-4X4", "Junction Box 4x4", "electrical", "each", 8.50, "Graybar", "JB-4X4", 3),
    ("ELE-JB-6X6", "Junction Box 6x6", "electrical", "each", 14.50, "Graybar", "JB-6X6", 3),
    ("ELE-DISC-60A", "Disconnect 60A", "electrical", "each", 65.00, "Graybar", "DISC-60", 5),
    ("ELE-GFI-20A", "GFI Outlet 20A", "electrical", "each", 25.00, "Graybar", "GFI-20", 3),
    ("ELE-TIMER", "Digital Timer", "electrical", "each", 85.00, "Graybar", "TIMER-DIG", 5),
    ("ELE-PHOTO", "Photocell", "electrical", "each", 35.00, "Graybar", "PHOTO-STD", 3),

    # Channel Letter Specifics
    ("CL-TRIM-4", "Channel Letter Trim 4\"", "channel_letters", "linear_ft", 2.25, "Gemini", "TRIM-4", 7),
    ("CL-TRIM-5", "Channel Letter Trim 5\"", "channel_letters", "linear_ft", 2.75, "Gemini", "TRIM-5", 7),
    ("CL-COIL-040", "Aluminum Coil .040", "channel_letters", "linear_ft", 1.85, "Gemini", "COIL-040", 5),
    ("CL-BACK-040", "Letter Back .040", "channel_letters", "sq_ft", 3.50, "Gemini", "BACK-040", 5),
    ("CL-FACE-ACR", "Acrylic Face Stock", "channel_letters", "sq_ft", 4.25, "Gemini", "FACE-ACR", 5),
    ("CL-STUD-MOUNT", "Stud Mount Kit", "channel_letters", "each", 1.25, "Gemini", "STUD-KIT", 3),
    ("CL-RACEWAY-4", "Raceway 4\"", "channel_letters", "linear_ft", 8.50, "Gemini", "RACE-4", 7),
    ("CL-RACEWAY-6", "Raceway 6\"", "channel_letters", "linear_ft", 12.50, "Gemini", "RACE-6", 7),
]


def seed_work_codes(engine):
    """Seed standard work codes."""
    logger.info("Seeding work codes...")

    with engine.connect() as conn:
        for code, description, category, rate, hours in WORK_CODES:
            try:
                conn.execute(text("""
                    INSERT INTO work_codes (code, description, category, default_rate, typical_hours, is_active, created_at, updated_at)
                    VALUES (:code, :description, :category, :rate, :hours, true, NOW(), NOW())
                    ON CONFLICT (code) DO UPDATE
                    SET description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        default_rate = EXCLUDED.default_rate,
                        typical_hours = EXCLUDED.typical_hours,
                        updated_at = NOW()
                """), {
                    'code': code,
                    'description': description,
                    'category': category,
                    'rate': rate,
                    'hours': hours,
                })
            except Exception as e:
                logger.error(f"Failed to insert work code {code}: {e}")

        conn.commit()

        result = conn.execute(text("SELECT COUNT(*) FROM work_codes"))
        count = result.scalar()
        logger.info(f"  Seeded {count} work codes")


def seed_material_catalog(engine):
    """Seed standard material catalog."""
    logger.info("Seeding material catalog...")

    with engine.connect() as conn:
        for part_num, desc, category, unit, cost, vendor, vendor_pn, lead_days in MATERIALS:
            try:
                conn.execute(text("""
                    INSERT INTO material_catalog (
                        part_number, description, category, unit, unit_cost,
                        preferred_vendor, vendor_part_number, lead_time_days,
                        is_active, is_taxable, created_at, updated_at, last_cost_update
                    )
                    VALUES (
                        :part_number, :description, :category, :unit, :cost,
                        :vendor, :vendor_pn, :lead_days,
                        true, true, NOW(), NOW(), NOW()
                    )
                    ON CONFLICT (part_number) DO UPDATE
                    SET description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        unit = EXCLUDED.unit,
                        unit_cost = EXCLUDED.unit_cost,
                        preferred_vendor = EXCLUDED.preferred_vendor,
                        vendor_part_number = EXCLUDED.vendor_part_number,
                        lead_time_days = EXCLUDED.lead_time_days,
                        updated_at = NOW(),
                        last_cost_update = NOW()
                """), {
                    'part_number': part_num,
                    'description': desc,
                    'category': category,
                    'unit': unit,
                    'cost': cost,
                    'vendor': vendor,
                    'vendor_pn': vendor_pn,
                    'lead_days': lead_days,
                })
            except Exception as e:
                logger.error(f"Failed to insert material {part_num}: {e}")

        conn.commit()

        result = conn.execute(text("SELECT COUNT(*) FROM material_catalog"))
        count = result.scalar()
        logger.info(f"  Seeded {count} materials")


def main():
    """Run the seed script."""
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://apex:apex@localhost:5432/apex"
    )

    logger.info("=" * 60)
    logger.info("SignX Estimator Catalog Seed")
    logger.info("=" * 60)
    logger.info(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
    logger.info("")

    engine = create_engine(DATABASE_URL)

    seed_work_codes(engine)
    seed_material_catalog(engine)

    logger.info("")
    logger.info("Seed complete.")


if __name__ == "__main__":
    main()
