import numpy as np  # Numerical computing library
# Importing Package to run CCA Algorithm
from biclustlib.algorithms import ChengChurchAlgorithm
from biclustlib.io import _biclustering_to_dict
import random as rd
import preprocessing



def logarithmic_transformation(data_test):
    # Do Logaritmic transformations on dataset that are suggested in the paper
    nonzero_mask = data_test != 0
    data_test_log_norm = np.zeros_like(data_test)
    data_test_log_norm[nonzero_mask] = np.log10(data_test[nonzero_mask] * (10**5)) * 100

    return data_test_log_norm


def get_sample(data_test, y_cat, sample_size=None):

    if not sample_size:
        return data_test, y_cat
    else:
        # Define sample of data to use CCA on smaller dataset.
        num_rows = len(data_test)
        random_indices = rd.sample(range(num_rows), sample_size)
        sample_data = data_test[random_indices]
        sample_labels = y_cat.iloc[random_indices]
        sample_labels = sample_labels.reset_index()

        print(sample_labels)

        return sample_data, sample_labels


def get_distribution_of_sample(sample_labels):

    labels = {"Normal": [], "Reconnaissance": [], "Backdoor": [], "DoS": [], "Exploits": [],
              "Analysis": [], "Fuzzers": [], "Worms": [], "Shellcode": [], "Generic": []}

    for label in labels:
        count = sample_labels["attack_cat"].value_counts().get(label, 0)
        labels[label] = count

    print(labels)


def run_cca(sample_data):
    # Run CCA on the sample data

    # missing value imputation suggested by Cheng and Church
    missing_sample = np.where(sample_data < 0.0)
    sample_data[missing_sample] = np.random.randint(low=0, high=800, size=len(missing_sample[0]))

    min_value = np.min(sample_data)
    max_value = np.max(sample_data)

    msr_thr = (((max_value - min_value) ** 2) / 12) * 0.005

    print(msr_thr)

    print("Initializing CCA")

    # creating an instance of the ChengChurchAlgorithm class and running with the parameters of the original study
    # cca = ChengChurchAlgorithm(num_biclusters=10, msr_threshold=300.0, multiple_node_deletion_threshold=1.2)

    cca = ChengChurchAlgorithm(num_biclusters=250)

    print("Starting Algorithm")
    biclustering_test = cca.run(sample_data)
    print(biclustering_test)

    return biclustering_test


def format_cca_results(biclustering_test, all_cat, sample_labels):
    biclusters_as_dict = _biclustering_to_dict(biclustering_test)
    results = []
    for bicluster in biclusters_as_dict["biclusters"]:
        bicluster_values = {}
        for cat in all_cat:
            bicluster_values[cat] = 0

        for row in bicluster[0]:
            bicluster_values[sample_labels.loc[row]["attack_cat"]] += 1

        results.append(bicluster_values)

    for result in results:
        print(result)

    return results


def calc_multi_classification(results):
    information = {}

    precision_numerator = 0
    precision_denominator = 0
    max_keys = set()

    for i, result in enumerate(results):
        max_key = max(result, key=result.get)
        max_keys.add(max_key)
        max_value = result[max_key]
        sum_values = sum(result.values())
        percent = (max_value / sum_values) * 100

        information[f"Bicluster {i + 1}"] = {
            "Sum": sum_values,
            "Max Key": max_key,
            "Percentage": percent
        }

        precision_numerator += result[max_key]
        precision_denominator += sum_values

    accuracy = precision_numerator / precision_denominator

    # print(information)
    print(max_keys)
    print("Accuracy Multiclassification:", accuracy)


def calculate_binary_classification(results):
    binary_results = []

    for result in results:
        binary_result = {
            "Normal": result.get("Normal", 0),
            "Attack": sum(value for key, value in result.items() if key != "Normal")
        }
        binary_results.append(binary_result)

    precision_numerator_binary = 0
    precision_denominator_binary = 0

    for j, binary_result in enumerate(binary_results):
        max_key_binary = max(binary_result, key=binary_result.get)
        max_value_binary = binary_result[max_key_binary]
        sum_values_binary = sum(binary_result.values())

        precision_numerator_binary += binary_result[max_key_binary]
        precision_denominator_binary += sum_values_binary

    accuracy_binary = precision_numerator_binary / precision_denominator_binary

    print("Accuracy binary:", accuracy_binary)


def main():
    data = preprocessing.preprocessing()
    test_data = data[1][0]
    y_cat_test = data[1][1]
    all_cat_test = data[1][2]
    test_data = logarithmic_transformation(test_data)
    sample_data, sample_labels = get_sample(test_data, y_cat_test, sample_size=500)
    get_distribution_of_sample(sample_labels)
    biclustering_test = run_cca(sample_data)
    results = format_cca_results(biclustering_test, all_cat_test, sample_labels)
    calc_multi_classification(results)
    calculate_binary_classification(results)


if __name__ == '__main__':
    main()
