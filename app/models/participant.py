from app import db


class Participant(db.Model):
    __tablename__ = 'participant'
    
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    
    team = db.relationship('Team', back_populates='participants')
    
    def getFullName(self):
        return f"{self.firstName} {self.lastName}"
