from psychopy import visual, core
from psychopy.hardware import keyboard
import numpy as np
from scipy import signal
import random, os

cyton_in = True
lsl_out = False
width = 1536
height = 864
refresh_rate = 60.02
stim_duration = 1.2
n_per_class = 2
stim_type = 'alternating' # 'alternating' or 'independent'
subject = 1
session = 1
training_mode = True
save_dir = f'data/cyton8_{stim_type}-vep_32-class_{stim_duration}s/sub-{subject:02d}/ses-{session:02d}/' # Directory to save data to
run = 1
save_file_eeg = save_dir + f'eeg_{n_per_class}-per-class_run-{run}.npy'
save_file_aux = save_dir + f'aux_{n_per_class}-per-class_run-{run}.npy'
save_file_timestamp = save_dir + f'timestamp_{n_per_class}-per-class_run-{run}.npy'
save_file_metadata = save_dir + f'metadata_{n_per_class}-per-class_run-{run}.npy'

if cyton_in:
    import glob, sys, time, serial
    from brainflow.board_shim import BoardShim, BrainFlowInputParams
    from serial import Serial
    from threading import Thread, Event
    from queue import Queue
    CYTON_BOARD_ID = 0 # 0 if no daisy 2 if use daisy board, 6 if using daisy+wifi shield
    BAUD_RATE = 115200
    ANALOGUE_MODE = '/2' # Reads from analog pins A5(D11), A6(D12) and if no 
                        # wifi shield is present, then A7(D13) as well.
    def find_openbci_port():
        """Finds the port to which the Cyton Dongle is connected to."""
        # Find serial port names per OS
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports = glob.glob('/dev/ttyUSB*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/cu.usbserial*')
        else:
            raise EnvironmentError('Error finding ports on your operating system')
        openbci_port = ''
        for port in ports:
            try:
                s = Serial(port=port, baudrate=BAUD_RATE, timeout=None)
                s.write(b'v')
                line = ''
                time.sleep(2)
                if s.inWaiting():
                    line = ''
                    c = ''
                    while '$$$' not in line:
                        c = s.read().decode('utf-8', errors='replace')
                        line += c
                    if 'OpenBCI' in line:
                        openbci_port = port
                s.close()
            except (OSError, serial.SerialException):
                pass
        if openbci_port == '':
            raise OSError('Cannot find OpenBCI port.')
            exit()
        else:
            return openbci_port
        
    print(BoardShim.get_board_descr(CYTON_BOARD_ID))
    params = BrainFlowInputParams()
    if CYTON_BOARD_ID != 6:
        params.serial_port = find_openbci_port()
    elif CYTON_BOARD_ID == 6:
        params.ip_port = 9000
    board = BoardShim(CYTON_BOARD_ID, params)
    board.prepare_session()
    res_query = board.config_board('/0')
    print(res_query)
    res_query = board.config_board('//')
    print(res_query)
    res_query = board.config_board(ANALOGUE_MODE)
    print(res_query)
    board.start_stream(45000)
    stop_event = Event()
    
    def get_data(queue_in, lsl_out=False):
        while not stop_event.is_set():
            data_in = board.get_board_data()
            timestamp_in = data_in[board.get_timestamp_channel(CYTON_BOARD_ID)]
            eeg_in = data_in[board.get_eeg_channels(CYTON_BOARD_ID)]
            aux_in = data_in[board.get_analog_channels(CYTON_BOARD_ID)]
            if len(timestamp_in) > 0:
                print('queue-in: ', eeg_in.shape, aux_in.shape, timestamp_in.shape)
                queue_in.put((eeg_in, aux_in, timestamp_in))
            time.sleep(0.1)
    
    queue_in = Queue()
    cyton_thread = Thread(target=get_data, args=(queue_in, lsl_out))
    cyton_thread.daemon = True
    cyton_thread.start()

# def create_32_targets(size=120, colors=[-1, -1, -1] * 32, checkered=False):
#     positions = []
#     positions.extend([[-width / 2 + 100, height / 2 - 90 - i * 200 - 80] for i in range(4)])
#     positions.extend([[-width / 2 + 190 * 1 + 100, height / 2 - 90 - i * 200 - 80] for i in range(4)])
#     positions.extend([[-width / 2 + 190 * 2 + 100, height / 2 - 90 - i * 200 - 80] for i in range(4)])
#     positions.extend([[-width / 2 + 190 * 3 + 100, height / 2 - 90 - i * 200 - 80] for i in range(4)])
#     positions.extend([[-width / 2 + 190 * 4 + 100, height / 2 - 90 - i * 200 - 80] for i in range(4)])
#     positions.extend([[-width / 2 + 190 * 5 + 100, height / 2 - 90 - i * 200 - 80] for i in range(4)])
#     positions.extend([[-width / 2 + 190 * 6 + 100, height / 2 - 90 - i * 200 - 80] for i in range(4)])
#     positions.extend([[-width / 2 + 190 * 7 + 100, height / 2 - 90 - i * 200 - 80] for i in range(4)])
#     if checkered:
#         texture = checkered_texure()
#     else:
#         texture = None
#     keys = visual.ElementArrayStim(window, nElements=32, elementTex=texture, elementMask=None, units='pix',
#                                    sizes=[size, size], xys=positions, colors=colors)
#     return keys

def create_32_targets(size=2/8*0.7, colors=[-1, -1, -1] * 32, checkered=False):
    size_with_border = size / 0.7
    width, height = window.size
    aspect_ratio = width/height
    positions = []
    for i_col in range(8):
        positions.extend([[i_col*size_with_border-1+size_with_border/2, -j_row*size_with_border*aspect_ratio+1-size_with_border*aspect_ratio/2 - 1/4/2] for j_row in range(4)])

    if checkered:
        texture = checkered_texure()
    else:
        texture = None
    keys = visual.ElementArrayStim(window, nElements=32, elementTex=texture, elementMask=None, units='norm',
                                   sizes=[size, size * aspect_ratio], xys=positions, colors=colors)
    return keys

def checkered_texure():
    rows = 8  # Replace with desired number of rows
    cols = 8  # Replace with desired number of columns
    array = np.zeros((rows, cols))
    for i in range(rows):
        array[i, ::2] = i % 2  # Set every other element to 0 or 1, alternating by row
        array[i, 1::2] = (i+1) % 2  # Set every other element to 0 or 1, alternating by row
    return np.kron(array, np.ones((16, 16)))*2-1

def create_photosensor_dot(size=2/8*0.7):
    width, height = window.size
    ratio = width/height
    return visual.Rect(win=window, units="norm", width=size, height=size * ratio, 
                       fillColor='white', lineWidth = 0, pos = [1 - size/2, -1 - size/8]
    )

def create_trial_sequence(n_per_class, classes=[(7.5, 0), (8.57, 0), (10, 0), (12, 0), (15, 0)], seed=0):
    """
    Create a random sequence of trials with n_per_class of each class
    Inputs:
        n_per_class : number of trials for each class
    Outputs:
        seq : (list of len(10 * n_per_class)) the trial sequence
    """
    seq = classes * n_per_class
    random.seed(seed)
    random.shuffle(seq)  # shuffles in-place
    return seq

keyboard = keyboard.Keyboard()
window = visual.Window(
        size = [width,height],
        checkTiming = True,
        allowGUI = False,
        fullscr = True,
        useRetina = False,
    )
visual_stimulus = create_32_targets(checkered=True)
photosensor_dot = create_photosensor_dot()
num_frames = np.round(stim_duration * refresh_rate).astype(int)  # total number of frames per trial
frame_indices = np.arange(num_frames)  # frame indices for the trial
if stim_type == 'alternating': # Alternating VEP (aka SSVEP)
    stimulus_classes = [(8, 0), (8, 0.5), (8, 1), (8, 1.5),
                        (9, 0), (9, 0.5), (9, 1), (9, 1.5),
                        (10, 0), (10, 0.5), (10, 1), (10, 1.5),
                        (11, 0), (11, 0.5), (11, 1), (11, 1.5),
                        (12, 0), (12, 0.5), (12, 1), (12, 1.5),
                        (13, 0), (13, 0.5), (13, 1), (13, 1.5),
                        (14, 0), (14, 0.5), (14, 1), (14, 1.5),
                        (15, 0), (15, 0.5), (15, 1), (15, 1.5), ] # flickering frequencies (in hz) and phase offsets (in pi*radians)
    stimulus_frames = np.zeros((num_frames, len(stimulus_classes)))
    for i_class, (flickering_freq, phase_offset) in enumerate(stimulus_classes):
            phase_offset += .00001  # nudge phase slightly from points of sudden jumps for offsets that are pi multiples
            stimulus_frames[:, i_class] = signal.square(2 * np.pi * flickering_freq * (frame_indices / refresh_rate) + phase_offset * np.pi)  # frequency approximation formula
trial_sequence = create_trial_sequence(n_per_class=1, classes=stimulus_classes, seed=0)

eeg = np.zeros((8, 0))
aux = np.zeros((3, 0))
timestamp = np.zeros((0))

if training_mode:
    visual_stimulus.colors = np.array([-1] * 3).T
    visual_stimulus.draw()
    photosensor_dot.color = np.array([-1, -1, -1])
    photosensor_dot.draw()
    window.flip()
    core.wait(1)
    for i_trial, (flickering_freq, phase_offset) in enumerate(trial_sequence):
        finished_displaying = False
        while not finished_displaying:
            for i_frame in range(num_frames):
                next_flip = window.getFutureFlipTime()
                keys = keyboard.getKeys()
                if 'escape' in keys:
                    if cyton_in:
                        os.makedirs(save_dir, exist_ok=True)
                        np.save(save_file_eeg, eeg)
                        np.save(save_file_aux, aux)
                        np.save(save_file_timestamp, timestamp)
                    core.quit()
                visual_stimulus.colors = np.array([stimulus_frames[i_frame]] * 3).T
                visual_stimulus.draw()
                photosensor_dot.color = np.array([1, 1, 1])
                photosensor_dot.draw()
                if core.getTime() > next_flip and i_frame != 0:
                    print('Missed frame')
                    visual_stimulus.colors = np.array([-1] * 3).T
                    visual_stimulus.draw()
                    photosensor_dot.color = np.array([-1, -1, -1])
                    photosensor_dot.draw()
                    window.flip()
                    core.wait(1)
                    break
                window.flip()
            finished_displaying = True
        visual_stimulus.colors = np.array([-1] * 3).T
        visual_stimulus.draw()
        photosensor_dot.color = np.array([-1, -1, -1])
        photosensor_dot.draw()
        window.flip()
        core.wait(1)
        if cyton_in:
            while not queue_in.empty():
                eeg_in, aux_in, timestamp_in = queue_in.get()
                print('data-in: ', eeg_in.shape, aux_in.shape, timestamp_in.shape)
                eeg = np.concatenate((eeg, eeg_in), axis=1)
                aux = np.concatenate((aux, aux_in), axis=1)
                timestamp = np.concatenate((timestamp, timestamp_in), axis=0)
            print('total: ',eeg.shape, aux.shape, timestamp.shape)
            # trial_eeg = np.copy(eeg[-100:])
            # trial_aux = np.copy(aux[-100:])
            # trial_timestamp = np.copy(timestamp)
            # print(trial_eeg.shape, trial_aux.shape, trial_timestamp.shape)
            # print(eeg.shape, aux.shape, timestamp.shape)
    if cyton_in:
        os.makedirs(save_dir, exist_ok=True)
        np.save(save_file_eeg, eeg)
        np.save(save_file_aux, aux)
        np.save(save_file_timestamp, timestamp)

else:
    while True:
        keys = keyboard.getKeys()
        if 'escape' in keys:
            core.quit()
        for i_frame in range(num_frames):
            visual_stimulus.colors = np.array([stimulus_frames[i_frame]] * 3).T
            visual_stimulus.draw()
            window.flip()
        core.wait(1)