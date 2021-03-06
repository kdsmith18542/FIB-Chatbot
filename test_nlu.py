from Fibot.NLP.nlu import NLU_unit
from pprint import pprint
from termcolor import colored
import numpy as np
import argparse

INTENT_AMOUNT = 14
SECOND_OKAY = 0
intent2idx = {
    'ask_teacher_mail': 0,
    'ask_teacher_office': 1,
    'ask_free_spots': 2,
    'ask_subject_classroom': 3,
    'ask_subject_schedule': 4,
    'ask_subject_teacher_mail': 5,
    'ask_subject_teacher_office': 6,
    'ask_subject_teacher_name': 7,
    'ask_next_class': 8,
    'ask_exams': 9,
    'ask_pracs': 10,
    'inform': 11,
    'greet': 12,
    'thank': 13
}
idx2intent = {
    0: 'ask_teacher_mail',
    1: 'ask_teacher_office',
    2: 'ask_free_spots',
    3: 'ask_subject_classroom',
    4: 'ask_subject_schedule',
    5: 'ask_subject_teacher_mail',
    6: 'ask_subject_teacher_office',
    7: 'ask_subject_teacher_name',
    8: 'ask_next_class',
    9: 'ask_exams',
    10: 'ask_pracs',
    11: 'inform',
    12: 'greet',
    13: 'thank'
}
intent_conf_matrix = np.zeros([INTENT_AMOUNT,INTENT_AMOUNT])

entity_report = {}

def conf2precision(conf_matrix):
    global intent2idx
    intents = intent2idx.keys()
    accuracy_dict = {}
    for intent in intents:
        row = intent2idx[intent]
        hits = conf_matrix[row][row]
        total = sum(conf_matrix[row])
        if total == 0: accuracy_dict[intent] = 0
        else: accuracy_dict[intent] = hits/total
    return accuracy_dict


def conf2recall(conf_matrix):
    global intent2idx
    intents = intent2idx.keys()
    recall_dict = {}
    for intent in intents:
        col = intent2idx[intent]
        hits = conf_matrix[col][col]
        total = sum(conf_matrix[:,col])
        if total == 0: recall_dict[intent] = 0
        else: recall_dict[intent] = hits/total
    return recall_dict


def print_conf_matrix(conf_matrix):
    global idx2intent
    for row in range(0, len(conf_matrix)):
        if row in [0,1,3,4]: fill = "\t\t"
        elif row in [2,8,9,10]: fill = "\t\t\t"
        elif row in [11, 12, 13]: fill = "\t\t\t\t"
        else: fill = "\t"
        print("{}:{}{}\t{}".format(idx2intent[row], fill, conf_matrix[row], int(sum(conf_matrix[row]))))


def get_global_accuracy(conf_matrix):
    return sum(conf_matrix.diagonal())/sum(sum(conf_matrix))


def get_avg_precision(conf_matrix):
    precisions = conf2precision(conf_matrix)
    val = list(precisions.values())
    return np.mean(val)


def get_avg_recall(conf_matrix):
    recalls = conf2recall(conf_matrix)
    val = list(recalls.values())
    return np.mean(val)


if __name__ == '__main__':
    nlu = NLU_unit()
    nlu.load()

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--lan',
                        nargs=1,
                        required = True,
                        choices=['ca','es','en'],
                        default = ['ca'],
                        help='Language for the interpretation')
    parser.add_argument('--file',
                        nargs=1,
                        required = False,
                        help='File for the interpreter to use')
    parser.add_argument('--stats',
                        nargs=1,
                        required = False,
                        choices = ['y', 'n'],
                        default = ['n'],
                        help='If the test has to output stats')
    parser.add_argument('--error',
                        nargs=1,
                        required=False,
                        choices = ['y', 'n'],
                        default = ['n'],
                        help ='If the test has to output errors')
    parser.add_argument('--entity',
                        nargs=1,
                        required=False,
                        choices = ['y', 'n'],
                        default = ['n'],
                        help ='If the test has to output errors')
    parser.add_argument('--filter',
                        nargs=1,
                        required=False,
                        type = str,
                        help ='If the test has to output errors')
    args = parser.parse_args()

    language = args.lan[0]
    if args.file: file_route = args.file[0]
    else: file_route = None
    if args.stats: stats = args.stats[0] == 'y'
    else: stats = False
    if args.error: error = args.error[0] == 'y'
    else: error = False
    if args.entity: entity = args.entity[0] == 'y'
    else: entity = False
    if args.filter: filter_intention = args.filter[0]
    else: filter_intention = None

    if not file_route:
        print("Para salir del modo de test escribe 'quit'")
        message = input("Introduce el mensaje:\n")
        while message != "quit":
            print("\n\nINFORMACIÓN DE MENSAJE: {}".format(colored(message, 'magenta')))
            print("__________________________________________")
            print("El intérprete ha predecido la siguiente intención:")
            intent = nlu.get_intent(message, language)
            entities = nlu.get_entities(message, language)
            print('Intención: ' + colored(intent['name'], 'green', attrs=['bold']))
            print('Confianza: ' + colored(str(intent['confidence'])[:8], 'green'))
            if entities: print("\nY las siguientes entidades:")
            else: print("\nNo se han encontrado entidades en el mensaje")
            i = 0
            for entity in entities:
            	print(colored('['+str(i)+']', 'red'))
            	print('Tipo: ' + colored(entity['entity'], 'cyan', attrs=['bold']))
            	print('Valor: ' + colored(entity['value'], 'cyan', attrs=['bold']))
            	print('Confianza: ' + colored(str(entity['confidence'])[:8], 'cyan'))
            	i+=1
            print("\n")
            if stats:
                hit = input("Está bien la intención? (y/n): ") == 'y'
                pred_intent = nlu.get_intent(message, language)['name']
                pred_idx = intent2idx[pred_intent]
                if hit: intent_conf_matrix[pred_idx][pred_idx] += 1
                else:
                    pprint(idx2intent)
                    ok_idx = -1
                    while not ok_idx in range(0,11):
                        ok_idx = input("Cuál de los anteriores es el correcto? (0..10)\n")
                        ok_idx = int(ok_idx)
                    intent_conf_matrix[ok_idx][pred_idx] += 1
            message = input("Introduce el mensaje:\n")
    else:
        avg_confidence_success = 0
        times_success = 0
        avg_confidence_failure = 0
        times_failure = 0
        with open(file_route, 'r') as file:
            contents = file.readlines()
            size = len(contents)
            for message_idx in range(0, size, 2):
                message = contents[message_idx].rstrip()
                ok_intent = contents[message_idx+1].rstrip()
                ok_idx = intent2idx[ok_intent]
                pred_intent = nlu.get_intent(message, language)['name']
                pred_idx = intent2idx[pred_intent]
                if entity:
                    entities = nlu.get_entities(message, language)
                    print("\n\n{}".format(message))
                    for ent in entities:
                        print("{} -> {}".format(ent['value'], ent['entity']))
                        if not ent['entity'] in entity_report.keys(): entity_report[ent['entity']] = 0
                        entity_report[ent['entity']] += 1
                if ok_idx != pred_idx:
                    pred_confidence = nlu.get_intent(message, language)['confidence']
                    avg_confidence_failure += pred_confidence
                    times_failure +=1
                    ranking = nlu.get_intent_ranking(message, language)
                    if intent2idx[ranking[1]['name']] == ok_idx:
                        SECOND_OKAY += 1
                    if error:
                        if not filter_intention:
                            print("\n\n{}: {} -> {} [{}]".format(message, ok_intent, pred_intent, pred_confidence))
                            print("La lista de alternativas es la siguiente:")
                            pprint(nlu.get_intent_ranking(message, language))
                        else:
                            if ok_intent == filter_intention:
                                print("\n\n{}: {} -> {} [{}]".format(message, ok_intent, pred_intent, pred_confidence))
                                print("La lista de alternativas es la siguiente:")
                                pprint(nlu.get_intent_ranking(message, language))
                else:
                    pred_confidence = nlu.get_intent(message, language)['confidence']
                    avg_confidence_success += pred_confidence
                    times_success +=1
                intent_conf_matrix[ok_idx][pred_idx] += 1
        avg_confidence_success = avg_confidence_success/times_success
        avg_confidence_failure = avg_confidence_failure/times_failure
        if stats:
            print("------------------------------------")
            print("\n\nRatio de éxito = {}/{}".format(times_success,(times_success+times_failure)))
            print("Confianza promedio en aciertos: {}".format(avg_confidence_success))
            print("Confianza promedio en fallos: {}".format(avg_confidence_failure))

    if stats:
        print("\n\nLa matriz de confusión resultante es la siguiente:")
        print_conf_matrix(intent_conf_matrix)
        print("\n\nLa precisión por intenciones es la siguiente:")
        pprint(conf2precision(intent_conf_matrix))
        print("\n\nEl recall por intenciones es la siguiente:")
        pprint(conf2recall(intent_conf_matrix))
        print("\n\nLa precisión global es de: {}".format(get_global_accuracy(intent_conf_matrix)))
        print("\n\nEn el {} por ciento de los errores, la segunda opción era la válida".format(SECOND_OKAY/times_failure))

    if entity:
        print("\n\nEl resultado en entidades es:")
        pprint(entity_report)
        print("\n\nEl total de entidades encontradas es:")
        print(sum(list(entity_report.values())))
