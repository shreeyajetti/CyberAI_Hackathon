## Audit Flow: Clinical-Billing Reconciliation Logic
This document outlines the step-by-step reasoning process used by the Doctor Nexus HMS agent to identify revenue leakage in tertiary care settings.

### 1. Contextual Data Ingestion
The agent begins by loading two disparate data sources into its transient reasoning memory:

The Clinical Truth (OT Logs): Unstructured text from surgeons, nurses, and technicians (e.g., "Deployed 2x Onyx Stents").

The Financial Record (Billing Invoice): Structured line items from the hospital's ERP/HMS (e.g., "Onyx Stent: Qty 1").

### 2. Semantic Entity Extraction
Unlike traditional regex-based systems, Doctor Nexus uses Medical LLM Reasoning to:

Identify Brands: Recognize that "Hem-o-lok" or "Echelon" refers to high-value surgical consumables.

Normalize Terms: Understand that "Ti Screw" (Note) maps to "Titanium Interference Screw" (Billing Code).

Deduce Implied Items: For example, if a "Total Hip Replacement" is noted, the agent automatically checks for "Bone Cement," which is frequently omitted from bills.

### 3. Cross-Reference & Gap Analysis
The agent performs a "Zero-Loss" comparison:

Quantity Check: Does the quantity in the note (e.g., 2x) match the quantity billed (1x)?

Omission Check: Is an item mentioned in the note (e.g., Bakri Balloon) completely absent from the bill?

Procedure Alignment: Does the billed procedure code match the complexity of the consumables used?

### 4. Leakage Valuation & Reporting
Once a gap is identified, the agent:

Estimates Value: Assigns a price based on the hospital's Master Price List.

Categorizes Risk: Flags "High-Certainty" leaks (Missing Implants) vs. "Low-Certainty" leaks (General Sutures).

Generates Recovery Table: Produces the final audit summary for the CFO/Admin.
