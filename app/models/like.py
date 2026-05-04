from libs.db import db
from datetime import datetime

class Like(db.Model):
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    regulation_id = db.Column(db.Integer, db.ForeignKey('regulations.id', ondelete='CASCADE'), nullable=True)
    training_program_id = db.Column(db.Integer, db.ForeignKey('training_programs.id', ondelete='CASCADE'), nullable=True)
    teaching_plan_id = db.Column(db.Integer, db.ForeignKey('teaching_plans.id', ondelete='CASCADE'), nullable=True)
    textbook_id = db.Column(db.Integer, db.ForeignKey('textbooks.id', ondelete='CASCADE'), nullable=True)
    courseware_id = db.Column(db.Integer, db.ForeignKey('coursewares.id', ondelete='CASCADE'), nullable=True)
    smart_resource_id = db.Column(db.Integer, db.ForeignKey('smart_resources.id', ondelete='CASCADE'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('regulation_id', 'user_id', name='unique_regulation_like'),
        db.UniqueConstraint('training_program_id', 'user_id', name='unique_training_program_like'),
        db.UniqueConstraint('teaching_plan_id', 'user_id', name='unique_teaching_plan_like'),
        db.UniqueConstraint('textbook_id', 'user_id', name='unique_textbook_like'),
        db.UniqueConstraint('courseware_id', 'user_id', name='unique_courseware_like'),
        db.UniqueConstraint('smart_resource_id', 'user_id', name='unique_smart_resource_like'),
        db.CheckConstraint(
            '(regulation_id IS NOT NULL AND training_program_id IS NULL AND teaching_plan_id IS NULL AND textbook_id IS NULL AND courseware_id IS NULL AND smart_resource_id IS NULL) OR '
            '(regulation_id IS NULL AND training_program_id IS NOT NULL AND teaching_plan_id IS NULL AND textbook_id IS NULL AND courseware_id IS NULL AND smart_resource_id IS NULL) OR '
            '(regulation_id IS NULL AND training_program_id IS NULL AND teaching_plan_id IS NOT NULL AND textbook_id IS NULL AND courseware_id IS NULL AND smart_resource_id IS NULL) OR '
            '(regulation_id IS NULL AND training_program_id IS NULL AND teaching_plan_id IS NULL AND textbook_id IS NOT NULL AND courseware_id IS NULL AND smart_resource_id IS NULL) OR '
            '(regulation_id IS NULL AND training_program_id IS NULL AND teaching_plan_id IS NULL AND textbook_id IS NULL AND courseware_id IS NOT NULL AND smart_resource_id IS NULL) OR '
            '(regulation_id IS NULL AND training_program_id IS NULL AND teaching_plan_id IS NULL AND textbook_id IS NULL AND courseware_id IS NULL AND smart_resource_id IS NOT NULL)',
            name='check_one_target'
            )
        )
