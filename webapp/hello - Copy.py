from flask import Flask, request, url_for, render_template,redirect
app = Flask(__name__)

from webUtils import webUtil


from flask.ext.babel import Babel, gettext as _
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
babel = Babel(app)

import logging
#from src.DB import SBDB
#from src.Utils import Util

@babel.localeselector
def get_locale():
    return webUtil.LANGUAGES[request.accept_languages.best_match(webUtil.g_listLangs)]

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/customer/known')
def customer_known():
    path=webUtil.GetLangDirFromRequest(request)+'/customer_known.html'
    return render_template(path)
    #return render_template("customer_known.html",template_folder=os.path.join(webUtil.GetLangDirFromRequest(request)))
    
@app.route('/customer/reset_password')
@app.route('/customer/reset_password/<code_uuid>',methods=["POST","GET"])
def customer_reset_password(code_uuid=None):
    return ""
'''
    if not SBDB.CheckRestoreUUID(code_uuid):
        return render_template('message.html',message=_("Error: invalid reset code!"))
    if request.method == 'POST':
        password=request.form['reg_password']
        if SBDB.RestorePasswordByUUID(code_uuid, Util.hash_password(password)):
            return render_template('message.html',message=_("Reset password success!"))
        else:
            return render_template('message.html',message=_("Error: Reset password fail!"))
    else:
        return render_template(webUtil.GetLangDirFromRequest(request)+'/customer/reset_password.html')
'''

if __name__ == '__main__':
    app.run(debug=True)