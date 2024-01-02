from flask import Flask, render_template, request, session, flash, send_from_directory, jsonify
import os, sqlite3, random

app = Flask(__name__)
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'87qsv54j7sd887qsd684788ts6df58dy8757s57d7jh7n7v7q8'

@app.route('/', methods=['GET', 'POST'])
@app.route('/enrol/', methods=['GET', 'POST']) # type: ignore
def enrol():
    l_error = ""
    if state() == 0:
        if request.method == 'GET':
            return render_template('enrol.html', namesWithoutPseudo = namesWithoutPseudo(), allNames = allNames())
        if request.method == 'POST':
            l_realname = request.form['realname']
            l_pseudo = request.form['pseudo']
            l_exclude = request.form['exclude']
            try :
                # Check si offre à sois meme
                if l_realname == l_exclude:
                    l_error = "Evidement que tu vas pas t'offrir un cadeau à toi même, boulet !"
                    raise AssertionError
                # Check si offre à un membre de la même famille
                if l_exclude != '':
                    l_query = str("SELECT family FROM people WHERE name = 'xxx_realname_xxx'").replace('xxx_realname_xxx', l_realname)
                    l_family = db(l_query)[0][0]
                    l_query = str("SELECT family FROM people WHERE name = 'xxx_exclude_xxx'").replace('xxx_exclude_xxx', l_exclude)
                    l_excludeFamily = db(l_query)[0][0]
                    if l_family == l_excludeFamily:
                        l_error = "Vous êtes déja dans la même famille"
                        raise AssertionError
                # On ajoute le pseudo
                l_query = str("""UPDATE people
                                 SET pseudo = 'xxx_pseudo_xxx'
                                 WHERE name = 'xxx_realname_xxx'""").replace('xxx_realname_xxx', l_realname).replace('xxx_pseudo_xxx', l_pseudo)
                db(l_query)
                # On ajoute l'exclude
                if l_exclude != '':
                    app.logger.info("Il y a un exclude")
                    l_query = str("SELECT id FROM people WHERE name = 'xxx_exclude_xxx'").replace('xxx_exclude_xxx', l_exclude)
                    l_excludeId = db(l_query)[0][0]
                    print(l_excludeId)
                    l_query = str("""UPDATE people
                                     SET exclude = xxx_exclude_xxx
                                     WHERE name = 'xxx_realname_xxx'""").replace('xxx_realname_xxx', l_realname).replace('xxx_exclude_xxx', str(l_excludeId))
                    db(l_query) 
                else:
                    app.logger.info("Pas d'exclude")
            except:
                app.logger.info('Query error')
                flash('Pas possible, ma bonne dame ... ' + l_error)
                return render_template('enrol.html', namesWithoutPseudo = namesWithoutPseudo(), allNames = allNames())
            else:
                flash("C'est fait !")
                return list()
    else:
        return render_template('notyet.html')

@app.route('/list/')
def list():
    if state() == 0:
        return render_template('list.html', persons = namesWithPseudo())
    else:
        return render_template('notyet.html')
    

@app.route('/delete/<int:id>')
def delete(id):
    l_query = str("UPDATE people SET pseudo = NULL, exclude = NULL WHERE id = xxx_id_xxx").replace("xxx_id_xxx", str(id))
    db(l_query)
    return list()

@app.route('/result/')
def result():
    if state() == 0:
        return render_template('notyet.html')
    else:
        return render_template('result.html', persons = associations())


@app.route('/admin/', methods=['GET', 'POST']) # type: ignore
def admin():
    return render_template('admin.html')

@app.route('/do/<int:id>')
def do(id):
    app.logger.info("Id : " + str(id))
    # Tirage
    if id == 1:
        boggle()
        return result()
    # Soft reset
    elif id == 2:
        softReset()
        return list()
    # Full reset
    elif id == 3:
        fullReset()
        return list()
    
def softReset():
    l_query = "UPDATE people SET target = NULL"
    db(l_query)
    l_query = "UPDATE config set value = 0 WHERE key = 'state'"
    db(l_query)

def fullReset():
    l_query = "UPDATE people SET target = NULL, pseudo = NULL, exclude = NULL"
    db(l_query)
    l_query = "UPDATE config set value = 0 WHERE key = 'state'"
    db(l_query)

def boggle():
    if state() != 0:
        return
    l_query = "SELECT id, family, exclude FROM people"
    l_liste = db(l_query)
    app.logger.info("Avant boggle" + str(l_liste))

    l_failed = True
    while l_failed:
        app.logger.info("Tentative" )
        l_failed = False
        # Créer une copie de la liste pour ne pas modifier l'originale
        l_data_copy = l_liste.copy()
        # Initialiser le dictionnaire pour stocker les associations id
        l_allocations = {}
        # Mélanger la liste de manière aléatoire
        random.shuffle(l_data_copy)
        # Associer les id de manière aléatoire en respectant la contrainte de groupe
        for id, family, exclude in l_data_copy:
            available_ids = [other_id for other_id, other_family, other_exclude in l_data_copy if other_family != family and other_id != exclude and other_id not in l_allocations.values()]
            # available_ids = [other_id for other_id, other_family in l_data_copy if other_family != family and other_id not in l_allocations.values()]
            if available_ids:
                allocated_id = random.choice(available_ids)
                l_allocations[id] = allocated_id
                l_data_copy = [(other_id, other_family, other_exclude) for other_id, other_family, other_exclude in l_data_copy if other_id != allocated_id]
            else:
                print("Impossible de respecter la contrainte de groupe.")
                l_failed = True
                break
    
    app.logger.info(l_allocations)
    
    for l_id in l_allocations.keys():
        l_query = str("UPDATE people SET target = xxx_target_xxx WHERE id = xxx_id_xxx").replace("xxx_target_xxx", str(l_allocations[l_id])).replace("xxx_id_xxx", str(l_id))
        db(l_query)

    l_query = "UPDATE config SET value = 1 WHERE key = 'state'"
    db(l_query)
    
    return

def state():
    l_query = "SELECT value FROM config WHERE key = 'state'"
    return int(db(l_query)[0][0])

def namesWithoutPseudo():
    l_query = "SELECT id, name, pseudo FROM people WHERE pseudo IS NULL ORDER BY name"
    return db(l_query)

def namesWithPseudo():
    l_query = """SELECT pp1.id, pp1.name, pp1.pseudo, pp2.name as exclude
                 FROM people pp1
                 LEFT JOIN people pp2 ON pp1.exclude = pp2.id
                 WHERE pp1.pseudo IS NOT NULL
                 ORDER BY pp1.name"""
    return db(l_query)

def allNames():
    l_query = "SELECT id, name, pseudo FROM people ORDER BY name"
    return db(l_query)

def associations():
    l_query = "SELECT pp1.pseudo, pp2.name FROM people pp1 INNER JOIN people pp2 ON pp1.target = pp2.id ORDER BY pp1.pseudo"
    return db(l_query)

def db(i_query):
    app.logger.info(i_query)
    con = sqlite3.connect("santa.db")
    cur = con.cursor()
    l_result = cur.execute(i_query).fetchall()
    con.commit()
    con.close()
    return l_result

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    app.run(debug=False)
