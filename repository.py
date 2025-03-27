import psycopg

"""работа с бд"""


class Repository:

    def __init__(self, my_dbname, my_user, my_password, my_host, my_port):
        self.dbname = my_dbname
        self.user = my_user
        self.password = my_password
        self.host = my_host
        self.port = my_port

    def psycopg_conn(self):
        return psycopg.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

    def get_subjects(self):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT id, name FROM subjects')
                subjects = cursor.fetchall()
        return subjects

    def add_user(self, userid):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE id = %s', (userid,))
                if not cursor.fetchone():
                    cursor.execute('INSERT INTO users (id) VALUES (%s)', (userid,))
                    conn.commit()

    def get_topics(self, subject_id):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT id, name FROM topics WHERE subject_id = %s', (subject_id,))
                topics = cursor.fetchall()

                cursor.execute('SELECT name FROM subjects WHERE id = %s', (subject_id,))
                subject_name = cursor.fetchone()

        return subject_name, topics

    def add_topic_to(self, topic_name, subject_id):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                            SELECT * FROM topics WHERE name = %s and subject_id = %s
                        ''', (topic_name, subject_id))
                if not cursor.fetchone():
                    cursor.execute('''
                                INSERT INTO topics (name, subject_id)
                                VALUES (%s, %s)''',
                                   (topic_name, subject_id))
                    conn.commit()
                    return True
                else:
                    return False

    def begin_photo_recieving(self, user_id, topic_id):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                            INSERT INTO abstracts (topic_id, user_id)
                            VALUES (%s, %s)
                            Returning id
                        ''', (topic_id, user_id))
                cursor.execute('''
                            SELECT id FROM abstracts WHERE user_id = %s AND topic_id = %s
                        ''', (user_id, topic_id))
                abstract_id = cursor.fetchone()[0]

                cursor.execute('''
                    INSERT INTO users (id, topic_id, abstract_id, state)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        topic_id = EXCLUDED.topic_id,
                        abstract_id = EXCLUDED.abstract_id,
                        state = EXCLUDED.state
                ''', (user_id, topic_id, abstract_id, "ожидание"))

                conn.commit()

    def check_the_user_status(self, user_id):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT topic_id, abstract_id, state FROM users WHERE id = %s', (user_id,))
                user_data = cursor.fetchone()
        return user_data

    def save_abstract(self, abstract_id, photo_path):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                            INSERT INTO photos (abstract_id, photo_path)
                            VALUES (%s, %s)
                        ''', (abstract_id, photo_path))
                conn.commit()

    def status_completed(self, user_id):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                            UPDATE users
                            SET state = %s
                            WHERE id = %s
                        ''', ("завершено", user_id))
                conn.commit()

    def availability_abstracts(self, topic_id):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                            SELECT abstracts.id 
                            FROM abstracts 
                            WHERE abstracts.topic_id = %s
                            ORDER BY created_at DESC
                        ''', (topic_id,))
                abstract_ids = cursor.fetchall()

        return abstract_ids

    def open_abstract(self, abstract_id):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                                SELECT photo_path 
                                FROM photos 
                                WHERE abstract_id = %s
                                ORDER BY created_at ASC
                            ''', (abstract_id,))
                photo_paths = cursor.fetchall()

        return photo_paths

    def cleanup_empty_abstracts(self):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    DELETE FROM abstracts
                    WHERE id NOT IN (
                        SELECT DISTINCT abstract_id FROM photos
                    )
                ''')
                conn.commit()

    def get_schedule_path(self, class_name):
        with self.psycopg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT schedule_path 
                    FROM additionally 
                    WHERE class_name = %s
                ''', (class_name,))
                result = cursor.fetchone()
        return result[0] if result else None
