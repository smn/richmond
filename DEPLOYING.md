Deploying Richmond
------------------

For deploying, updating, starting & stopping of services we use [Fabric][fabric].

Start the virtualenv & make sure all the requirements are installed:

    $ source ve/bin/activate
    
There are two environments, `staging` & `production`. They'll be installed in `/var/praekelt/richmond/`. For this example we'll walk through installing a `staging` environment.

Before we start update the `fabfile.py` and change `env.hosts` to point to the machine you're deploying to.

To start the deploy execute the following:

    (ve) $ fab deploy:staging
    ...
    
Internally this first calls `fab layout_directories:staging` to create the following layout directory:

    .
    └── richmond
        └── staging
            ├── releases            # all timestamped releases go here
            └── shared              # all shared stuff that needs to be kept
                ├── logs            # across releases is stored here.
                ├── repositories
                └── tmp
                    ├── cache
                    │   └── pip
                    └── pids

Then it continues to checkout the repository into `staging/shared/repositories/richmond` and switches to the branch `staging`. If the repository already exists it instead does a `git pull` to pull in the latest updates.

Then it creates a new timestamped release folder in `releases` and copies the cloned GIT repository into it.

Next it'll call `fab setup_virtualenv:staging` to setup the virtualenv in the latest release folder. Setting up the `virtualenv` will download all the project dependencies and install them. Remember that `libcurl-dev` is needed for the `pycurl` library to compile.

Next the latest release will be symlinked to `staging/current`. Nginx will point to whatever app is running inside `current`.

After this you'll probably want to setup the database. In my case I'm using psyopg2 and it's not in the requirements file, I'll have to install that manually too.

    (ve) $ fab execute:staging,"pip -E ve install pyscopg2"
    (ve) $ fab execute:staging,"./manage.py syncdb"

If you'd want to deploy some minor code change then use `fab update:staging`, that'll pull in the latest changes. Remember to restart the webapp for the changes in the code to be picked up.

Starting, restarting & stopping the webapp
------------------------------------------

By default the webapp will start on port 8000. You can specify which port you want. The port is used as the unique identifier for the process, it's used for naming the PID. You can start multiple instances by specifying different ports.

    (ve) $ fab start_webapp:staging,port=8001
    (ve) $ fab restart_webapp:staging,port=8001
    (ve) $ fab stop_webapp:staging,port=8001


Deploying other environments
----------------------------

Other environments work exactly the same:

    (ve) $ fab deploy:production

Will deploy to `/var/praekelt/richmond/production` with the same directory layout. It'll switch to the `production` branch in the git repository.

[fabric]: http://www.fabfile.org