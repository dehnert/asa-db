import subprocess

MMBLANCHE_PATH="/mit/consult/bin/mmblanche"

class MailmanList():
    def __init__(self, name, ):
        self.name = name

    def list_members(self, ):
        res = subprocess.Popen(
            [MMBLANCHE_PATH, self.name, ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = res.communicate()
        if res.returncode:
            raise RuntimeError("Failed to list members: %s" % (stderr, ))
        members = stdout.strip().split("\n")
        return members

    def change_members(self, add_members, delete_members, ):
        """
        Add and/or remove members from the list.
        """

        # Note that it passes all members on the commandline, so it shouldn't be
        # used for large lists at the moment. OTOH, "large" appears to be
        # 2M characters, so.
        # If that becomes an issue, it should probably check the number of
        # changes, and use -al / -dl with a tempfile as appropriate.

        cmdline = [MMBLANCHE_PATH, self.name, ]
        for member in add_members:
            cmdline.append('-a')
            if type(member) == type(()):
                name, email = member
                name = name.replace('"', "''")
                member = '"%s" <%s>' % (name, email, )
            cmdline.append(member)
        for member in delete_members:
            cmdline.append('-d')
            cmdline.append(member)
        res = subprocess.Popen(
            cmdline,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = res.communicate()
        assert stderr==""
        return stdout
