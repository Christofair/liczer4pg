"""Manager who can create all models or drop whole database without droping db itself."""
import sqlalchemy as sa
import liczer4pg.models as models
import sys, os
from datetime import datetime


# if __name__ == '__main__':
#     login, password = ('','')
#     try:
#         with open('.mylogin.cnf') as dbkey:
#             _, login, password = dbkey.read().splitlines()
#             login = login.split('=')[1]
#             password = password.split('=')[1]
#     except OSError:
#         print("Opening DBKEY file failed.")
#         print('Ending.')
#         exit(-1)
#     if len(sys.argv) <= 1:
#         print("usage: python dbmanager.py (create|drop|export)")
#         exit(0)
#     engine = sa.create_engine(
#                     f"mysql+pymysql://{login}:{password}@localhost/TyperkaPG")
#     if sys.argv[1] == "create":
#         models.Base.metadata.create_all(engine)
#     elif sys.argv[1] == "drop":
#         response = input('Are you sure?> ')
#         if ('y' in response or 'Y' in response) and len(response) == 1:
#             models.Base.metadata.drop_all(engine)
#     else:
#         print("Command not found.")
    # elif sys.argv[1] == "export":
    #     if len(sys.argv) <= 2:
    #         filename = input('Enter filename: ')
    #         if not filename.endswith('.sql'):
    #             filename = f"{filename}.sql"
    #     else:
    #         filename = sys.argv[2]
    #         if not filename.endswith('.sql'):
    #             filename = f"{filename}.sql"
    #     print(f"{password}")
    #     os.system('"A:\\Program Files\\mysql-8.0.22-winx64\\bin\\mysqldump.exe" ' 
    #                f'-u {login} -password {password} typerkapg > {filename}')


class DBManager:
    """I will see of using this"""

    def __init__(self):
        login, password = ('','')
        try:
            with open('.mylogin.cnf') as dbkey:
                _, login, password = dbkey.read().splitlines()
                login = login.split('=')[1]
                password = password.split('=')[1]
                self.db_ready = True
        except OSError:
            print("Opening config file failed.")
            self.db_ready = False
        # engine = sa.create_engine(f"mysql+pymysql://{login}:{password}@localhost/TyperkaPG")
        engine = sa.create_engine("sqlite:///ddd.db")
        self.db_ready = True
        self.session_maker = sa.orm.sessionmaker(bind=engine)

    def session(self):
        if self.db_ready:
            return self.session_maker()
        else:
            raise ValueError("DB was not initialized well")

    def get_years_from_events(self):
        """Collect distinct years from events"""
        stmt = sa.select(models.Event.start_time.year).distinct

    def get_all_typers_names(self):
        """Retrieve typers names from database"""
        stmt = sa.select(models.Typer.name)
        with self.session() as session:
            result = session.execute(stmt).scalars().all()
        return result

    def get_typer_id_by_name(self, typername):
        stmt = sa.select(models.Typer.id).where(models.Typer.name == typername)
        with self.session() as session:
            result = session.execute(stmt)
        return result.id

    def get_bets_typers_with_topicname(self):
        """Get bets with typername and topicname"""
        stmt = sa.select(models.Bet).join(models.Topic.name, models.Topic.sport, models.Typer.name)
        with self.session() as session:
            result = session.execute(stmt)
        return result

    def get_bets_typer_by_month(self, date: datetime):
        """Get typer and his bets from month"""
        # stmt = (sa.select(models.Typer, models.Typer.bets, models.Bet.events)
        #         .join(models.Event.bet).join(models.Bet.typer)
        #         .where(models.Event.start_time.month == date.month)
        #         .where(models.Event.start_time.year == date.year))
        # stmt = (sa.select(models.Typer).where(models.Typer.name.like('%sto%')))
        # with self.session() as session:
        #     result = session.execute(stmt)
        # return result
