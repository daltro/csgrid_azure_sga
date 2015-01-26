

__author__ = 'daltrogama'

import string
import random
import os
from zipfile import ZipFile

class SandboxManager():

    def __init__(self, config, connector):
        self.algorithm_root = config.get("sga", "algorithm_root")
        self.project_root = config.get("sga", "project_root")
        self.connector = connector
        return


    def get_algorithm(self, algorithm_bin_file):

        tmp_file = os.tempnam()
        res_dir = os.path.join(self.algorithm_root, algorithm_bin_file)
        os.mkdir(res_dir)

        self.connector.download_algo_zip(algorithm_bin_file, tmp_file)

        zipf = ZipFile(name=tmp_file)
        try:
            zipf.extractall(path=res_dir)
            zipf.close()
        finally:
            zipf.close()

        os.remove(tmp_file)

        return res_dir


    def get_project(self, project_prfx, project_input_files):

        proj_sandbox = os.path.join(self.project_root, project_prfx)

        for f in project_input_files:
            self.connector.download_file_to_project(project_prfx, f, proj_sandbox)

        return proj_sandbox


    def upload_project_modified_files(self, project_prfx):
        return


    def __get_hash_of_dirs(directory, verbose=0):
      import hashlib, os
      sha_hash = hashlib.sha1()
      if not os.path.exists (directory):
        return -1

      try:
        for root, dirs, files in os.walk(directory):
          for names in files:
            if verbose == 1:
              print 'Hashing', names
            filepath = os.path.join(root,names)
            try:
              f1 = open(filepath, 'rb')
            except:
              # You can't open the file for some reason
              f1.close()
              continue

        while 1:
          # Read file in as little chunks
          buf = f1.read(4096)
          if not buf : break
          sha_hash.update(hashlib.sha1(buf).hexdigest())
        f1.close()

      except:
        import traceback
        # Print the stack traceback
        traceback.print_exc()
        return -2

      return sha_hash.hexdigest()
