"""Manager who can create all models or drop whole database without droping db itself."""
import sqlalchemy
import models
import sys, os


if __name__ == '__main__':
    login, password = ('','')
    try:
        with open('.mylogin.cnf') as dbkey:
            _, login, password = dbkey.read().splitlines()
            login = login.split('=')[1]
            password = password.split('=')[1]
    except OSError:
        print("Opening DBKEY file failed.")
        print('Ending.')
        exit(-1)
    if len(sys.argv) <= 1:
        print("usage: python dbmanager.py (create|drop|export)")
        exit(0)
    engine = sqlalchemy.create_engine(
                    f"mysql+pymysql://{login}:{password}@localhost/TyperkaPG")
    if sys.argv[1] == "create":
        models.Base.metadata.create_all(engine)
    elif sys.argv[1] == "drop":
        response = input('Are you sure?> ')
        if ('y' in response or 'Y' in response) and len(response) == 1:
            models.Base.metadata.drop_all(engine)
    else:
        print("Command not found.")
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
