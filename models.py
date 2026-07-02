from django.db import models


# ============================================================
# VC / ASN MASTER
# ============================================================
#
# This table stores the production plan received from the MES.
#
# Every record represents ONE planned vehicle.
#
# Example
#
# VC      : VC1001
# ASN     : ASN5001
# MODEL   : NEXON
#
# Operator selects one row from this table.
#
# Once the trolley is scanned,
# ONE AsnSchedule (Execution) is created.
#
# ============================================================

class vc_n_asn(models.Model):

    id = models.BigAutoField(primary_key=True)

    # MES Information
    vc_no = models.CharField(max_length=50)

    asn_no = models.CharField(max_length=50)

    model = models.CharField(max_length=150)

    schedule_date_time = models.DateTimeField()

    # 0 = Not Started
    # 1 = In Process
    # 2 = Completed
    status = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vc_n_asn"

    def __str__(self):
        return f"{self.vc_no} - {self.asn_no}"


# ============================================================
# VC MASTER / PART MASTER
# ============================================================
#
# Stores all part mappings of a VC.
#
# Used for payload generation.
#
# VC
#    ↓
# Payload
#    ↓
# WorkTable
#
# ============================================================


class VcMaster(models.Model):
    """
    VC Master

    Stores the vehicle model corresponding
    to a VC Number.

    VC123
        ↓
    NEXON

    Used only for displaying model
    and joining with VC.
    """

    id = models.BigAutoField(primary_key=True)

    vcnumber = models.CharField(
        max_length=50,
        unique=True
    )

    model = models.CharField(max_length=150)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vc_master"

    def __str__(self):
        return self.vcnumber


class EslPart(models.Model):
    """
    Maps one Part to one ESL.

    VC is NOT stored here.

    Part Number comes through VcDatabase.
    """

    id = models.BigAutoField(primary_key=True)

    vc_part = models.ForeignKey(
        VcDatabase,
        on_delete=models.CASCADE,
        related_name="esl_part"
    )

    rack = models.CharField(max_length=10)

    sequence = models.IntegerField()

    row = models.IntegerField()

    side = models.CharField(max_length=10)

    tag_mac = models.CharField(max_length=50)

    tag_name = models.CharField(max_length=100)

    tag_code = models.CharField(max_length=100)

    max_quantity = models.IntegerField()

    class Meta:
        db_table = "esl_part"

    def __str__(self):
        return self.tag_mac



class VcDatabase(models.Model):

    id = models.BigAutoField(primary_key=True)

    vc_master = models.ForeignKey(
        VcMaster,
        on_delete=models.CASCADE,
        related_name="parts"
    )

    part_number = models.CharField(max_length=100)

    description = models.TextField()

    quantity = models.IntegerField()

    mapping_type = models.IntegerField()

    style_id = models.IntegerField()

    led_state = models.IntegerField(default=0)

    led_rgb = models.CharField(max_length=20)

    out_time = models.IntegerField(default=0)

    class Meta:
        db_table = "vc_database"

# ============================================================
# ASN SCHEDULE
# ============================================================
#
# THIS IS THE MASTER OF ONE KITTING EXECUTION
#
# Flow
#
# MES
#      ↓
# vc_n_asn
#      ↓
# Operator Selects VC
#      ↓
# Scan Trolley
#      ↓
# Create AsnSchedule
#
#
# Every WorkTable created during this execution
# belongs to THIS AsnSchedule.
#
#
# Even if ASN repeats tomorrow,
#
# a NEW AsnSchedule is created.
#
# ============================================================

class AsnSchedule(models.Model):

    id = models.BigAutoField(primary_key=True)

    # Parent MES Record
    mes_record = models.ForeignKey(
        vc_n_asn,
        on_delete=models.PROTECT,
        related_name="executions"
    )

    # Copy of MES Information
        mes_record = models.ForeignKey(
        vc_n_asn,
        on_delete=models.PROTECT,
        related_name="executions"
    )
    
    vc_master = models.ForeignKey(
        VcMaster,
        on_delete=models.PROTECT,
        related_name="executions"
    )

    # Trolley Information
    trolley_code = models.CharField(max_length=50)

    trolley_qr = models.CharField(max_length=50)

    # Execution Color
    color = models.CharField(max_length=20)

    # Pending
    # In Process
    # Completed
    selection_status = models.CharField(
        max_length=30,
        default="Pending"
    )

    bypass_status = models.BooleanField(default=False)

    start_time = models.DateTimeField()

    end_time = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "asn_schedule"

    def __str__(self):
        return f"{self.asn_no}"


# ============================================================
# TROLLEY MASTER
# ============================================================
#
# Stores all trolleys available in the system.
#
# One trolley can work on only one
# AsnSchedule at a time.
#
# ============================================================

class trolley_data(models.Model):

    id = models.BigAutoField(primary_key=True)

    trolley_code = models.CharField(max_length=50)

    trolley_qr = models.CharField(max_length=50)

    mac = models.CharField(max_length=50)

    color = models.CharField(max_length=20)

    trolley_picking_status = models.CharField(
        max_length=30,
        default="Available"
    )

    current_asn_schedule = models.ForeignKey(
        AsnSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trolleys"
    )

    class Meta:
        db_table = "trolley_data"

    def __str__(self):
        return self.trolley_code


# ============================================================
# WORK TABLE
# ============================================================
#
# THIS TABLE STORES ACTUAL WORK
#
# One row = One ESL Tag
#
#
# Example
#
# AsnSchedule
#
#      ASN100
#
#          │
#
#          ▼
#
# -------------------------
# WorkTable
# -------------------------
#
# MAC1
# MAC2
# MAC3
# MAC4
# MAC5
#
#
# Router callback updates ONLY this table.
#
#
# Once ALL rows become completed,
#
# AsnSchedule becomes completed.
#
#
# IMPORTANT
#
# Every WorkTable belongs to ONE AsnSchedule.
#
# This removes repeated ASN problems.
#
# ============================================================

class WorkTable(models.Model):

    id = models.BigAutoField(primary_key=True)

    # Parent Execution
    asn_schedule = models.ForeignKey(
        AsnSchedule,
        on_delete=models.CASCADE,
        related_name="work_items"
    )

    # Redundant fields kept for reporting/search
    vc_no = models.CharField(max_length=50)

    asn_no = models.CharField(max_length=50)

    color = models.CharField(max_length=20)

    # ESL Information
    tag_mac = models.CharField(max_length=50)

    tag_code = models.CharField(max_length=50)

    tag_name = models.CharField(max_length=100)

    # Part Information
    part_number = models.CharField(max_length=100)

    part_description = models.TextField()

    quantity = models.IntegerField()

    # Work Status
    # Pending
    # Completed
    status = models.CharField(
        max_length=20,
        default="Pending"
    )

    started_at = models.DateTimeField()

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    retry_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "work_table"

    def __str__(self):
        return f"{self.part_number} ({self.status})"
