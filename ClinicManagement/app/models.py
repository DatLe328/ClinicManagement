from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, Enum, Date, Time
from sqlalchemy.orm import relationship
from app import db, app
from enum import Enum as RoleEnum
from flask_login import UserMixin
from datetime import datetime, date


class UserRole(RoleEnum):
    USER = 1
    CASHIER = 2
    NURSE = 3
    DOCTOR = 4
    ADMIN = 5


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class MedicineCategory(BaseModel):
    category_name = Column(String(50), nullable=False)
    medicines = relationship('Medicine', backref='medicine_category', lazy=True)

    def __str__(self):
        return self.category_name


class Medicine(BaseModel):
    name = Column(String(50), nullable=False)
    price = Column(Float, default=0)
    unit = Column(String(50))
    status = Column(Boolean, default=True)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey(MedicineCategory.id), nullable=False)
    prescription_details = relationship('PrescriptionDetail', backref='medicine', lazy=True)

    def __str__(self):
        return self.name


class User(BaseModel, UserMixin):
    full_name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    birth_date = Column(Date, default=datetime.now())
    gender = Column(Boolean, nullable=True)
    phone_number = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(100), nullable=True)
    avatar = Column(String(100), nullable=False)
    status = Column(Boolean, default=True)
    user_role = Column(Enum(UserRole), default=UserRole.USER)
    prescriptions = relationship("Prescription", backref="user", lazy=True)
    invoices = relationship("Invoice", backref="user", lazy=True)
    appointment_list_details = relationship("AppointmentDetail", backref="user", lazy=True)
    medical_history = relationship("MedicalHistory", backref="user", lazy=True, uselist=False)

    def __str__(self):
        return self.full_name


class Invoice(BaseModel):
    name = Column(String(50), default="Invoice", nullable=False)
    date = Column(Date, default=datetime.now())
    payment_completed = Column(Boolean, default=False)
    total_amount = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)

    def __str__(self):
        return self.name


class Prescription(BaseModel):
    name = Column(String(50), default="Prescription", nullable=False)
    date = Column(Date, default=datetime.now())
    symptoms = Column(String(100), nullable=True)
    diagnosis = Column(String(100), nullable=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)

    def __str__(self):
        return self.name


class PrescriptionDetail(BaseModel):
    quantity = Column(Integer, nullable=True)
    medicine_id = Column(Integer, ForeignKey(Medicine.id), nullable=False)
    prescription_id = Column(Integer, ForeignKey(Prescription.id), nullable=False)


class AppointmentList(BaseModel):
    name = Column(String(50), default="Appointment List", nullable=True)
    date = Column(Date, default=datetime.now())

    def __str__(self):
        return self.name


class AppointmentDetail(BaseModel):
    time = Column(Time, nullable=True)
    appointment_list_id = Column(Integer, ForeignKey(AppointmentList.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


class Disease(BaseModel):
    name = Column(String(50), nullable=True)
    medical_history_details = relationship("MedicalHistoryDetail", backref="disease", lazy=True)

    def __str__(self):
        return self.name


class MedicalHistory(BaseModel):
    name = Column(String(50), default="Medical History", nullable=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    history_details = relationship("MedicalHistoryDetail", backref="medical_history", lazy=True)

    def __str__(self):
        return self.name


class MedicalHistoryDetail(BaseModel):
    medical_history_id = Column(Integer, ForeignKey(MedicalHistory.id), nullable=False)
    disease_id = Column(Integer, ForeignKey(Disease.id), nullable=False)



if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        import hashlib

        password = "123"
        password_admin = "123"
        password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
        password_admin = str(hashlib.md5(password_admin.encode('utf-8')).hexdigest())

        u1 = User(full_name="Lê Văn Đạt", username="admin", password=password_admin, gender=True,
                  phone_number="0123", address="Ho Chi Minh City", email='hoquochuy99.2019@gmail.com',
                  avatar="https://res.cloudinary.com/dvy7nvssm/image/upload/v1735196752/syfud0anik9cqtjgxsps.jpg", user_role=UserRole.ADMIN)
        u2 = User(full_name="Hồ Quốc Huy", username="cashier", password=password, gender=False,
                  phone_number="0124", address="Ho Chi Minh City",
                  avatar="https://res.cloudinary.com/dvy7nvssm/image/upload/v1735196752/syfud0anik9cqtjgxsps.jpg", user_role=UserRole.CASHIER)
        u3 = User(full_name="Lê Nguyễn Đức Huy", username="nurse", password=password, gender=False,
                  phone_number="0125", address="Ho Chi Minh City",
                  avatar="https://res.cloudinary.com/dvy7nvssm/image/upload/v1735196868/d8egzpstsk60zluk5sza.jpg", user_role=UserRole.NURSE)
        u4 = User(full_name="Lưu Quang Tạ", username="doctor", password=password, gender=True, phone_number="0126",
                  address="Ho Chi Minh City",
                  avatar="https://res.cloudinary.com/dvy7nvssm/image/upload/v1735196868/d8egzpstsk60zluk5sza.jpg", user_role=UserRole.DOCTOR)
        u5 = User(full_name="Bùi Thùy Dương", username="user", password=password, gender=False, phone_number="0127",
                  address="Ho Chi Minh City",
                  avatar="https://res.cloudinary.com/dvy7nvssm/image/upload/v1735196868/d8egzpstsk60zluk5sza.jpg", user_role=UserRole.USER)
        u6 = User(full_name="Tăng Duy Tân", username="user1", password=password, gender=True, phone_number="0128",
                  address="Phu Nhuan",
                  avatar="https://res.cloudinary.com/dvy7nvssm/image/upload/v1735196752/syfud0anik9cqtjgxsps.jpg", user_role=UserRole.USER)


        mc1 = MedicineCategory(category_name="Thuốc dạng lỏng")
        mc2 = MedicineCategory(category_name="Thuốc dạng viên")
        mc3 = MedicineCategory(category_name="Thuốc dạng bột")


        m1 = Medicine(name="Paracetamol", price=50000, unit="Viên", description="1 lần 1 ngày", category_id=2)
        m2 = Medicine(name="Vitamin C", price=10000, unit="Viên", description="2 lần 1 ngày", category_id=2)
        m3 = Medicine(name="Y", price=5000, unit="Milli", description="3 lần 1 ngày", category_id=1)
        m4 = Medicine(name="Sensacool", price=20000, unit="Viên", description="2 lần 1 ngày", category_id=3)
        m5 = Medicine(name="Adrenaline", price=30000, unit="Viên", description="2 lần 1 ngày", category_id=3)
        m6 = Medicine(name="Probiotic", price=15000, unit="Viên", description="2 lần 1 ngày", category_id=3)

        p1 = Prescription(name="Prescription 1", symptoms="Đau bụng", diagnosis="Viêm loét dạ dày", user_id=3, date=date(2024,1,1))
        p2 = Prescription(name="Prescription 2", symptoms="Đau vai", diagnosis="Thoái hoá cột sống", user_id=4,date=date(2024,1,1))
        p3 = Prescription(name="Prescription 3", symptoms="Đau tim", diagnosis="Nhồi máu cơ tim", user_id=5,date=date(2024,1,2))

        pd1_p1 = PrescriptionDetail(quantity=3, medicine_id=3, prescription_id=1)
        pd2_p1 = PrescriptionDetail(quantity=2, medicine_id=5, prescription_id=1)
        pd3_p1 = PrescriptionDetail(quantity=10, medicine_id=6, prescription_id=1)
        pd1_p2 = PrescriptionDetail(quantity=5, medicine_id=6, prescription_id=2)
        pd2_p2 = PrescriptionDetail(quantity=4, medicine_id=4, prescription_id=2)
        pd1_p3 = PrescriptionDetail(quantity=8, medicine_id=2, prescription_id=3)
        pd2_p3 = PrescriptionDetail(quantity=15, medicine_id=6, prescription_id=3)

        al1 = AppointmentList(name="Appointment List 1", date=date(2024,1,1))
        al2 = AppointmentList(name="Appointment List 2", date=date(2024,1,2))

        ald1_al1 = AppointmentDetail(appointment_list_id=1, user_id=3)
        ald2_al1 = AppointmentDetail(appointment_list_id=1, user_id=4)
        ald1_al2 = AppointmentDetail(appointment_list_id=2, user_id=5)

        d1 = Disease(name="Đau lưng")
        d2 = Disease(name="Đau đầu")
        d3 = Disease(name="Đau bụng")
        d4 = Disease(name="Đau răng")
        d5 = Disease(name="Đau tim")

        mh1 = MedicalHistory(name="Medical History 1", user_id=3)
        mh2 = MedicalHistory(name="Medical History 2", user_id=4)
        mh3 = MedicalHistory(name="Medical History 3", user_id=5)


        mhd1_mh1 = MedicalHistoryDetail(medical_history_id=1, disease_id=1)
        mhd2_mh1 = MedicalHistoryDetail(medical_history_id=1, disease_id=2)
        mhd3_mh1 = MedicalHistoryDetail(medical_history_id=2, disease_id=3)
        mhd1_mh2 = MedicalHistoryDetail(medical_history_id=2, disease_id=4)
        mhd2_mh2 = MedicalHistoryDetail(medical_history_id=2, disease_id=5)
        mhd1_mh3 = MedicalHistoryDetail(medical_history_id=3, disease_id=5)

        i1 = Invoice(name="Invoice 1", total_amount=1000000, user_id=3, date=date(2024, 1, 1))
        i2 = Invoice(name="Invoice 2", total_amount=2000000, user_id=4, date=date(2024, 1, 1))
        i3 = Invoice(name="Invoice 3", total_amount=4000000, user_id=5, date=date(2024, 1, 2))

        db.session.add_all([u1, u2, u3, u4, u5, u6])
        db.session.add_all([mc1, mc2, mc3])
        db.session.add_all([m1, m2, m3, m4, m5, m6])
        db.session.add_all([d1, d2, d3, d4, d5])
        db.session.add_all([p1, p2, p3])
        db.session.add_all([pd1_p1, pd2_p1, pd3_p1, pd1_p2, pd2_p2, pd1_p3, pd2_p3])
        db.session.add_all([al1, al2])
        db.session.add_all([ald1_al1, ald2_al1, ald1_al2])
        db.session.add_all([mh1, mh2, mh3])
        db.session.add_all([mhd1_mh1, mhd2_mh1, mhd3_mh1, mhd1_mh2, mhd2_mh2, mhd1_mh3])
        db.session.add_all([i1, i2, i3])


        db.session.commit()
