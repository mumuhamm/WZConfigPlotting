#!/usr/bin/env python
"""
  Modified from T. Ruggles, U. Wisconsin
"""
import glob
import imghdr
import argparse

def writeHTML(path, include_pdfs):
    image_files = [x for x in glob.glob(path + "/*.*") if imghdr.what(x)]
    if include_pdfs:
        pdfs = [x for x in glob.glob(path + "/*.*") if "pdf" in x]
        image_files += pdfs

    with open('%s/index.html' % path, 'w') as index:
        index = open('%s/index.html' % path, 'w')
        index.write( '<html><head><STYLE type="text/css">img { border:0px; }</STYLE>\n' )
        index.write( '<title>webView</title></head>\n' )
        index.write( '<body>\n' )
        for image_file in image_files :
            file_name = image_file.strip().split('/')[-1].strip() 
            if "pdf" in image_file:
                index.write('<embed src=%s width="500" height="500" type="application/pdf">\n' % file_name)
            else:
                index.write( '<img src="%s">\n' % file_name)
        index.write( '</body></html>' )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--include_pdfs', action='store_true')
    parser.add_argument('-p', '--path_to_files', type=str, required=True)
    args = parser.parse_args()

    writeHTML(args.path_to_files.rstrip("/*"), args.include_pdfs)

if __name__ == "__main__":
    main()
