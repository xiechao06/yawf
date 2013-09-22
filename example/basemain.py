#! /usr/bin/env python
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, current_app, flash
from flask.ext.login import current_user, login_required, LoginManager, login_user, logout_user
from flask.ext.wtf import Form
from wtforms import TextField
from wtforms.validators import DataRequired
from sqlalchemy.orm.exc import NoResultFound
import yawf
import yawf.exceptions
import yawf.constants

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "ieyaxuqu"
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///temp.db'


login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(user_id)
login_manager.login_view = "login"

from database import sa_db
import models
from yawf import WorkFlowEngine, register_policy
WorkFlowEngine(sa_db, models.Node)
import yawf.models
from yawf.utils import do_commit

class Travel(yawf.Policy):

    @property
    def dependencies(self):
        return [("PermitTravel", 
                 {
                     'name': 'permit travel application',
                     'handler_group': models.Group.query.filter(models.Group.name=='Clerks').one(),
                     'tag': self.node.tag,
                 }
                )]

register_policy(Travel)

class PermitTravel(yawf.Policy):

    pass

register_policy(PermitTravel)

@app.route("/")
def index():
    return redirect(url_for('node_list_view'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    class _Form(Form):
        username = TextField('username', validators=[DataRequired()])
    form = _Form()
    if form.validate_on_submit():
        try:
            user = models.User.query.filter(models.User.username==form.username.data).one()
        except NoResultFound:
            return render_template('login.html', form=form, error='no such user "%s"' % form.username.data )
        login_user(user) 
        return redirect(request.args.get('next'))
    return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    try:
        logout_user()
    except Exception: # in case sesson expire
        pass

    next_url = request.args.get("next", "/")
    return redirect(next_url)

@app.route("/node", methods=["GET", "POST"])
@login_required
def node_view():
    
    class _Form(Form):
        destination = TextField('destination', validators=[DataRequired()])
        contact = TextField('contact', validators=[DataRequired()])

    form = _Form()

    if form.validate_on_submit():
        work_flow = yawf.new_work_flow('travel application', 
                      lambda work_flow: models.Node(name='Submit Travel Application', policy_name="Travel", work_flow=work_flow, 
                                     handler_group=models.Group.query.filter(models.Group.name=='Customers').one()),
                      lambda work_flow: do_commit(models.Application(username=current_user.username, 
                                  destination=form.destination.data, 
                                  contact=form.contact.data, 
                                  work_flow=work_flow)).id)
        try:
            work_flow.start()
        except yawf.exceptions.WorkFlowDelayed:
            flash('You have just submitted an travel application')
            return redirect(url_for('node_list_view'))
    return render_template('/request.html', form=form)

@app.route("/node-list", methods=["GET", "POST"])
@login_required
def node_list_view():
    node_list = models.Node.query.filter(models.Node.handler_group_id==current_user.group.id)
    data = []
    for node in node_list:
        application = models.Application.query.get(node.tag)
        d = {}
        d['annotation'] = ', '.join([application.destination, application.username, application.contact])
        d['work_flow'] = node.work_flow
        d['name'] = node.name
        d['create_time'] = node.create_time
        d['handle_time'] = node.handle_time
        data.append(d)
    return render_template('/node-list.html', node_list=data, constants=yawf.constants)

@app.route('/process-node/<id_>', methods=['POST'])
@login_required
def process_node(id_):
    action = request.args['action'].lower()
    if action not in {'permit', 'refuse'}:
        return "", 403
    node = models.Node.query.get(id_)
    if action == 'permit':
        node.approve()
    elif action == 'refuse':
        node.refuse()
    return ''
