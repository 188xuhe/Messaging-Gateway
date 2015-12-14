

import logging
from webUtils import webUtil

from flask import Flask, request, url_for, render_template,redirect
app = Flask(__name__)

from flask.ext.babel import Babel, gettext as _
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
babel = Babel(app)

from src.DB import SBDB
from src.Utils import Util

@babel.localeselector
def get_locale():
    return webUtil.LANGUAGES[request.accept_languages.best_match(webUtil.g_listLangs)]

@app.route('/')
def hello_world():
    return 'Honeywell Smart Home!'


@app.route('/customer/known')
def customer_known():
    return render_template(webUtil.GetLangDirFromRequest(request)+'/customer/known.html')
    #return render_template("customer_known.html",template_folder=os.path.join(webUtil.GetLangDirFromRequest(request)))
    
@app.route('/customer/reset_password',methods=["POST","GET"])
@app.route('/customer/reset_password/<code_uuid>',methods=["POST","GET"])
def customer_reset_password(code_uuid=None):
    print "code_uuid:",code_uuid
    if request.method == 'POST':
        code_uuid=request.form['code_uuid']
        password=request.form['reg_password']
        
        if len(password)<20 and SBDB.RestorePasswordByUUID(code_uuid, Util.hash_password(password)):
            return render_template('message.html',message=_("Reset password success!"))
        else:
            return render_template('message.html',message=_("Error: Reset password fail!"))
    if not SBDB.CheckRestoreUUID(code_uuid):
        return render_template('message.html',message=_("Error: invalid reset code!"))
    else:
        return render_template(webUtil.GetLangDirFromRequest(request)+'/customer/reset_password.html',code_uuid=code_uuid)


if __name__ == '__main__':
    logging.basicConfig(filename='example.log',level=logging.INFO,format="%(asctime)s-%(name)s-%(levelname)s-%(message)s")
    app.run(debug=True)