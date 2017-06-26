
"""PMRReader by DJFio.
   Some Example code for testing and understanding the module

.. MDV website:
   http://djfio.ru/mdv/
"""
import os
import Tkinter as tk
import tkFileDialog
import PMR


def example(filename):
    """working example"""
    print 'testing %s version %s' % (PMR.__name__, PMR.__version__)
    PMR.__module_encodind__ = 'iso8859_5'
    test = PMR.PMRreader("file://"+filename)
    print "Number Of Items:", test.numberofitemsinpmr
    print "UUID Size In Bytes:", test.uuidlength
    print "Contents size:", test.datalength
    print "Printable Data:\n"
    print test.outprintable()
    print "XML Data:\n"
    xmldata = test.outxml()
    xmldata[:] = sorted(xmldata, key=lambda child: child.get("matUUID"))
    print PMR.prettify(xmldata)




# lets add some GUI stuff

# Make a top-level instance and hide since it is ugly and big.
root = tk.Tk()
root.withdraw()

# Make it almost invisible - no decorations, 0 size, top center.
root.overrideredirect(True)
cx = root.winfo_screenwidth() / 2
root.geometry("0x0+%d+0" % (cx))

# Show window again and lift it to top so it can get focus,
# otherwise dialogs will end up behind the terminal.
root.deiconify()
root.lift()
root.focus_force()

if  os.name == "posix":
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

fname = tkFileDialog.askopenfilename(parent=root) # Ok, finally give me the name

# Get rid of the top-level instance once to make it actually invisible.
root.destroy()

# test here
example(fname)
# end test

