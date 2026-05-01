from sqlalchemy.orm import Session

from backend.models.user import UserProfile


DEFAULT_USER_ID = 1


def get_user(db: Session) -> UserProfile | None:
    return db.query(UserProfile).filter(UserProfile.id == DEFAULT_USER_ID).first()


def update_user(db: Session, data: dict) -> UserProfile:
    user = get_user(db)
    if not user:
        user = UserProfile(id=DEFAULT_USER_ID)
        db.add(user)
    for key, value in data.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
