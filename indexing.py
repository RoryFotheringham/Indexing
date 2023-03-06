import os
import xml.etree.ElementTree as ET
from Index import Index


def create_index(data_dir, fileout):
    files = os.scandir(data_dir)

    # num of docs term appears in
    term_freq = {}
    # docs that a term appears in
    term_doc_appearances = {}
    # positions of appearances of term in each doc
    term_positions = {}
    term_doc_sv = {}
    # term_doc_videos = {}
    doc_no = 1
    sv_no = 1
    for f in files:
        if "xml" not in f.name:
            continue
        inp_dir = data_dir + f.name
        print("===============================================")
        print(inp_dir)
        print(doc_no)
        doc_no, sv_no = create_index_xml(inp_dir, doc_no, term_freq, term_doc_appearances, term_positions, term_doc_sv,
                                         sv_no)
        # exit()

    with open(fileout, 'w', encoding='utf-8') as w:
        w.write(f"num_docs: {doc_no}\n")
        for k in sorted(term_freq):
            # print(f"{k}: {term_freq[k]}")
            w.write(f"{k}: {term_freq[k]}\n")
            for doc in sorted(term_doc_appearances[k]):
                line = f"\t{doc}: "
                # print(f"{doc}: {term_positions[(k, doc)]}")
                for pos in term_positions[(k, doc)]:
                    line += f"{pos},"
                line = f"{line[:-1]}\n"
                w.write(line)


def create_index_xml(filein, doc_no, term_freq, term_doc_appearances, term_positions, term_doc_sv, sv_no):
    tree = ET.parse(filein)
    root = tree.getroot()
    # print(root.tag)

    for elem in root:
        # print("=======")
        # print(elem.tag)
        if elem.tag == "source":
            source = elem.text
            continue
        elif elem.tag == "date":
            date = elem.text
            continue
        elif elem.tag == "course":
            continue
        elif elem.tag == "lectures":
            max_doc_no, sv_no = indexLecturesElem(elem, doc_no, term_freq, term_doc_appearances, term_positions,
                                                  term_doc_sv, sv_no)
        elif elem.tag == "videos":
            continue

    return max_doc_no + 1, sv_no


def index_sv_text(slide_text, doc_no, dictionary, sv_no):
    """_summary_ adds a slide number to the (slide|video)_term_doc dictionary 
    for each term

    Args:
        dictionary (dict): either the (slide|video)_term_doc <term:<doc:[slide|video]>> 
        doc_no (_type_): _description_
        counter (_type_): _description_
        term_freq (_type_): _description_
        

    Returns:
        _type_: _description_
    """
    # doc_no = lecture_no + int(slide_no.text)
    # if (current_doc_no != doc_no+lecture_no):
    #     print(doc_no+lecture_no, "-", lecture_title)
    if not slide_text.text:
        return sv_no
    # for clean data
    tokens = slide_text.text.split(" ")
    # for only tokenizing and case folding
    # tokens = preprocessing.tokenize(subelem.text.lower())
    for t in tokens:
        # add term to doc appearance dictionary
        if t in dictionary:
            if dictionary[t].get(doc_no):
                dictionary[t][doc_no].append(sv_no)
            else:
                dictionary[t].update({doc_no: [sv_no]})
        else:
            dictionary[t] = {doc_no: [sv_no]}

    sv_no += 1
    return sv_no


def indexText(slide_text, doc_no, counter, term_freq, term_doc_appearances, term_positions):
    # doc_no = lecture_no + int(slide_no.text)
    # if (current_doc_no != doc_no+lecture_no):
    #     print(doc_no+lecture_no, "-", lecture_title)
    if not slide_text.text:
        return counter
    # for clean data
    tokens = slide_text.text.split(" ")
    # for only tokenizing and case folding
    # tokens = preprocessing.tokenize(subelem.text.lower())
    for t in tokens:
        # add term to doc appearance dictionary
        if t in term_doc_appearances:
            term_doc_appearances[t].add(doc_no)
        else:
            term_doc_appearances[t] = {doc_no}

        # add term to frequency dictionary
        term_freq[t] = len(term_doc_appearances[t])

        # add term to positions dictionary
        if (t, doc_no) in term_positions:
            term_positions[(t, doc_no)].append(counter)
        else:
            term_positions[(t, doc_no)] = [counter]

        counter += 1
    return counter


def indexLecturesElem(root, doc_no, term_freq, term_doc_appearances, term_positions, term_doc_sv, sv_no):
    lecture_no = doc_no - 1
    counter = 1
    for lecture_elem in root:
        if lecture_elem.tag != "lecture":
            continue
        for elem in lecture_elem:
            # print("=======")
            # print(elem.tag)
            if elem.tag == "lecture_title":
                lecture_title = elem.text
            elif elem.tag == "lectureno":
                lecture_no += 1
                print(lecture_no, "-", lecture_title)
                # lecture_no = int(elem.text)
            elif elem.tag == "slides":

                for subelem in elem:
                    print(f'\t\tslide_video_number: {sv_no}')
                    slide_no, slide_text = list(subelem)
                    # print(f"Slide {slide_no.text.strip()}")
                    sv_no = index_sv_text(slide_text, lecture_no, term_doc_sv, sv_no)
                    counter = indexText(slide_text, lecture_no, counter, term_freq, term_doc_appearances,
                                        term_positions)

            elif elem.tag == "videos":
                # local_video_no = 1

                for subelem in elem:
                    video_url, video_title, video_transcript = list(subelem)
                    print(f'\t\tslide_video_number: {sv_no}')
                    # print(f"Video - {video_title.text}")
                    for video_slice in video_transcript:
                        time_slice, slice_text = list(video_slice)
                        sv_no = index_sv_text(slice_text, lecture_no, term_doc_sv, sv_no)
                        counter = indexText(slice_text, lecture_no, counter, term_freq, term_doc_appearances,
                                            term_positions)
            else:
                continue
            """
            counter = 1
            for subelem in elem:
                # print(subelem.tag, len(subelem.text))
                slide_no, slidetext = list(subelem)

                # doc_no = lecture_no + int(slide_no.text)
                current_doc_no = doc_no + lecture_no
                max_doc_no = max(max_doc_no, current_doc_no)

                if not slidetext.text:
                    continue
                # for clean data
                tokens = slidetext.text.split(" ")
                # for only tokenizing and casefolding
                # tokens = preprocessing.tokenize(subelem.text.lower())
                for t in tokens:
                    # add term to doc appearance dictionary
                    if t in term_doc_appearances:
                        term_doc_appearances[t].add(current_doc_no)
                    else:
                        term_doc_appearances[t] = {current_doc_no}

                    # add term to frequency dictionary
                    term_freq[t] = len(term_doc_appearances[t])

                    # add term to positions dictionary
                    if (t, current_doc_no) in term_positions:
                        term_positions[(t, current_doc_no)].append(counter)
                    else:
                        term_positions[(t, current_doc_no)] = [counter]
                    counter += 1
            """
    return lecture_no, sv_no


def load_index(filein):
    term_freq = {}
    term_doc_appearances = {}
    term_positions = {}
    with open(filein, "r", encoding='utf-8') as f:
        num_docs = int(f.readline().split(" ")[1].strip())
        return Index(filein, num_docs)
        for line in f:
            if line[0] != '\t':
                terms = line.split(": ")
                term_freq[terms[0]] = int(terms[1])
                key = terms[0]
                # print("-----------")
                # print("header:", repr(terms[0]), repr(int(terms[1])))
            # print(repr(line))
            else:
                terms = line.split(": ")
                doc = int(terms[0])
                if key in term_doc_appearances:
                    term_doc_appearances[key].add(doc)
                else:
                    term_doc_appearances[key] = {doc}

                positions = [int(s) for s in terms[1].split(',')]
                term_positions[(key, doc)] = set(positions)
                # print("footer:", repr(int(terms[0])), repr(positions))

    return Index(filein, num_docs, term_freq, term_doc_appearances, term_positions)
