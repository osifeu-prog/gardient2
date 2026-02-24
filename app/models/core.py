from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Text, BigInteger, UniqueConstraint
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)  # telegram user_id
    chat_id = Column(BigInteger, nullable=True)
    username = Column(String(128), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event = Column(String(64), nullable=False)
    actor_user_id = Column(BigInteger, nullable=True)
    meta = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RewardLedger(Base):
    __tablename__ = "reward_ledger"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    currency = Column(String(16), nullable=False, default="ZUZ")
    amount = Column(Integer, nullable=False)
    reason = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ExpertCategory(Base):
    __tablename__ = "expert_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(64), unique=True, nullable=False)
    title = Column(String(128), nullable=False)

class ExpertCandidate(Base):
    __tablename__ = "expert_candidates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    category_id = Column(Integer, ForeignKey("expert_categories.id"), nullable=False)
    bio = Column(Text, nullable=True)
    __table_args__ = (UniqueConstraint("user_id", "category_id", name="uq_candidate"),)

class ExpertVote(Base):
    __tablename__ = "expert_votes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    voter_user_id = Column(BigInteger, nullable=False)
    candidate_id = Column(Integer, ForeignKey("expert_candidates.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("voter_user_id", "candidate_id", name="uq_vote"),)

class P2POrder(Base):
    __tablename__ = "p2p_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_user_id = Column(BigInteger, nullable=False)
    token = Column(String(16), nullable=False, default="SLH")
    amount = Column(Integer, nullable=False)
    price_currency = Column(String(16), nullable=False, default="ZUZ")
    price_total = Column(Integer, nullable=False)
    status = Column(String(16), nullable=False, default="OPEN")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ManagedGroup(Base):
    __tablename__ = "managed_groups"
    id = Column(BigInteger, primary_key=True)  # telegram chat_id
    title = Column(String(256), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())