import base64
import io
import os.path
import PIL.Image
import PySimpleGUI as sg
import definitions
from shutil import copy


def convert_to_bytes(file_or_bytes, resize=None):
    '''
    Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
    Turns into  PNG format in the process so that can be displayed by tkinter
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :type file_or_bytes:  (Union[str, bytes])
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    :return: (bytes) a byte-string object
    :rtype: (bytes)
    '''
    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    else:
        try:
            img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            dataBytesIO = io.BytesIO(file_or_bytes)
            img = PIL.Image.open(dataBytesIO)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height / cur_height, new_width / cur_width)
        img = img.resize((int(cur_width * scale), int(cur_height * scale)), PIL.Image.ANTIALIAS)
    with io.BytesIO() as bio:
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()


def title_bar(title, text_color, background_color):
    """
    Creates a "row" that can be added to a layout. This row looks like a titlebar
    :param title: The "title" to show in the titlebar
    :type title: str
    :param text_color: Text color for titlebar
    :type text_color: str
    :param background_color: Background color for titlebar
    :type background_color: str
    :return: A list of elements (i.e. a "row" for a layout)
    :rtype: List[sg.Element]
    """
    bc = background_color
    tc = text_color
    font = 'Helvetica 12'

    return [sg.Col([[sg.T(title, text_color=tc, background_color=bc, font=font, grab=True)]], pad=(0, 0),
                   background_color=bc),
            sg.Col([[sg.T('_', text_color=tc, background_color=bc, enable_events=True, font=font, key='-MINIMIZE-'),
                     sg.Text('❎', text_color=tc, background_color=bc, font=font, enable_events=True, key='Exit')]],
                   element_justification='r', key='-C-', grab=True,
                   pad=(0, 0), background_color=bc)]


def prepare_image_name(image):
    index_start = image.rfind("\\")
    index_end = image.rfind(".")
    return image[index_start + 1:index_end]


def open_window_for_players(background_image, new_size=None):
    background_layout = [[sg.Image(data=convert_to_bytes(background_image, resize=new_size), key='-IMG PLAYERS-')],
                         [sg.Button(button_text='Fit to window', key='-RESIZE')]]

    window_background = sg.Window('Map', background_layout, finalize=True, margins=(0, 0),
                                  element_padding=(0, 0), right_click_menu=[[''], ['Exit', ]], resizable=True,
                                  element_justification='center')

    return window_background


def open_main_window():
    left_col = [[sg.Text('Folder'), sg.Input(size=(25, 1), enable_events=True, key='-FOLDER-'), sg.FolderBrowse(),
                 sg.Button('Default')],
                [sg.Listbox(values=[], enable_events=True, size=(20, 20), key='-FILE LIST-')],
                [sg.Submit(button_text='Remove file', key='-REMOVE FILE-'), sg.Text('Resize to'),
                 sg.In(key='-W-', size=(5, 1)), sg.In(key='-H-', size=(5, 1))]]

    # For now will only show the name of the file that was chosen
    images_col = [[sg.Text(' ')],
                  [sg.Image(key='-IMAGE-')]]

    # ----- Full layout -----
    layout = [
        [sg.Column(left_col, element_justification='c'),
         sg.VSeperator(),
         sg.Column(images_col, element_justification='c')]]

    return sg.Window('Dungeon Explorer', layout, resizable=True, finalize=True)


def get_filenames(folder):
    try:
        file_list = os.listdir(folder)  # get list of files in folder
    except:
        file_list = []
    fnames = [f for f in file_list if os.path.isfile(
        os.path.join(folder, f)) and f.lower().endswith((".png", ".jpg", "jpeg", ".tiff", ".bmp"))]

    return fnames


def set_default_directory(window):
    fnames = get_filenames(definitions.MAPS_DIR)
    window['-FOLDER-'].update(value=definitions.MAPS_DIR)
    window['-FILE LIST-'].update(fnames)


def maximize_image(event):
    if window.TKroot.state() == 'zoomed':
        print("My window is maximized")


window1 = open_main_window()
window2 = None
filename = None

set_default_directory(window1)

while True:
    window, event, values = sg.read_all_windows()
    if event == sg.WIN_CLOSED or event == 'Exit':
        window.close()
        if window == window2:
            window2 = None
        elif window == window1:
            break
    if event == 'Default':
        set_default_directory(window)
    if event == '-SUBMIT SAVE-':
        file = window['-SAVE FILE-'].get()
        copy(file, definitions.MAPS_DIR)
        window['-SAVE FILE-'].update(value='')
    if event == '-REMOVE FILE-' and filename is not None:
        os.remove(filename)
    if event == '-FOLDER-':  # Folder name was filled in, make a list of files in the folder
        folder = values['-FOLDER-']
        fnames = get_filenames(folder)
        window['-FILE LIST-'].update(fnames)
    if event == '-RESIZE':
        window['-IMG PLAYERS-'].update(convert_to_bytes(filename, resize=window.size))
        window1['-IMAGE-'].update(convert_to_bytes(filename, resize=window1.size))
    elif event == '-FILE LIST-':  # A file was chosen from the listbox
        try:
            filename = os.path.join(values['-FOLDER-'], values['-FILE LIST-'][0])
            if values['-W-'] and values['-H-']:
                new_size = int(values['-W-']), int(values['-H-'])
            else:
                new_size = int(1200), int(800)
            window['-IMAGE-'].update(data=convert_to_bytes(filename, resize=new_size))
            window2 = open_window_for_players(filename, new_size)
        except Exception as E:
            print(f'** Error {E} **')
            pass  # something weird happened making the full filename
# --------------------------------- Close & Exit ---------------------------------
window.close()
