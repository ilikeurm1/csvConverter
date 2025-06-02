import csv
import os
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd  # type: ignore
import json

# Path to the directory containing the CSV files
PATH = "measurements"
WRITEPATH = "converted_measurements"

# Ensure the output directory exists
if not os.path.exists(WRITEPATH):
    os.makedirs(WRITEPATH)

def get_csv_files(directory: str) -> list[str]:
    """Get a list of all CSV files in the specified directory.

    Args:
        directory (str): The directory to search for CSV files.

    Returns:
        list[str]: A list of CSV file names.
    """
    return [f for f in os.listdir(directory) if f.endswith(".csv")]

def get_first_line_info(file_path: str) -> tuple[str, str]:
    """Get the starting time from the first row of a CSV file.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        tuple[str, str]: The title and starting time of the measurement.
    """
    with open(file_path, "r") as rf:
        reader = csv.reader(rf)
        title = next(reader)[0]  # Read the first line (title)
        date, time = (
            title.split(" ", 1)[1].rsplit(" ", 1)[0].split()[2:]
        )  # Get the date and time from the title by removing the first and last part

    return title, date + " " + time

def create_writable_list(file_path: str, headers: list[str], t0: datetime.datetime) -> list:
    # Create the dictionary that can be written to a CSV file
    csv_list: list[dict[str, str | int]] = []

    with open(file_path, "r") as rf:
        reader = csv.reader(rf)
        lines = list(reader)[1:]  # Skip the first line (title)
        for il, line in enumerate(lines):
            # CO2 = line[0].split(":")[-1]
            # TEMP = line[1].split(":")[-1]
            # MAX_CO2 = line[2].split(":")[-1]
            # MIN_CO2 = line[3].split(":")[-1]
            # TIME = (t0 + datetime.timedelta(seconds=(il)*2)).strftime("%Y.%m.%d %H:%M:%S")
            # data = [CO2, TEMP, MAX_CO2, MIN_CO2, TIME]
            data = [d.split(":")[-1].strip() for d in line]
            data.append(
                (t0 + datetime.timedelta(seconds=(il) * 2)).strftime(
                    "%Y.%m.%d %H:%M:%S"
                )
            )

            for ih, header in enumerate(headers):
                if ih == 0:
                    csv_list.append({header: data[ih]})
                else:
                    csv_list[il][header] = data[ih]

    return csv_list


def load_config(config_path: str = "cfg.json") -> dict:
    """Load configuration from JSON file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: Configuration dictionary with list-based structure.
    """
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(
            f"Warning: Could not load config file {config_path}. Skipping detailed plots."
        )
        return {}


def load_config_csv(config_path: str = "cfg.csv") -> dict:
    """Load configuration from CSV file.

    Args:
        config_path (str): Path to the CSV configuration file.

    Returns:
        dict: Configuration dictionary with list-based structure.
    """
    try:
        config = {"detailed_plots": []}
        
        with open(config_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                plot_config = {
                    "file": row["File"],
                    "from": row["Start"],
                    "length": row["Duration"]
                }
                config["detailed_plots"].append(plot_config)
        
        return config
        
    except (FileNotFoundError, csv.Error) as e:
        print(f"Warning: Could not load CSV config file {config_path}: {e}")
        return {}


def parse_time_duration(duration_str: str) -> datetime.timedelta:
    """Parse time duration string in format 'hh:mm' to timedelta.

    Args:
        duration_str (str): Duration in format 'hh:mm'

    Returns:
        datetime.timedelta: Parsed duration
    """
    hours, minutes = map(int, duration_str.split(":"))
    return datetime.timedelta(hours=hours, minutes=minutes)


def plot_detailed_co2_data(
    converted_files_path: str = WRITEPATH,
    config_path: str = "cfg.json",
    csv_config_path: str = "cfg.csv",
    detailed_plots_folder: str = "detailed_plots",
):
    """Plot detailed CO2 levels based on configuration file.

    Args:
        converted_files_path (str): Path to directory containing converted CSV files.
        config_path (str): Path to configuration JSON file.
        csv_config_path (str): Path to configuration CSV file.
        detailed_plots_folder (str): Folder name to save detailed plots in.
    """
    # Try to load configuration from JSON first, then CSV
    config = load_config(config_path)
    if not config.get("detailed_plots"):
        config = load_config_csv(csv_config_path)
    
    detailed_config = config.get("detailed_plots", [])

    if not detailed_config:
        print("No detailed plot configuration found. Skipping detailed plots.")
        return

    # Create detailed plots directory if it doesn't exist
    if not os.path.exists(detailed_plots_folder):
        os.makedirs(detailed_plots_folder)

    for plot_config in detailed_config:
        csv_filename = plot_config["file"]
        converted_filename = f"converted_{csv_filename}"
        file_path = os.path.join(converted_files_path, converted_filename)

        # Check if converted file exists
        if not os.path.exists(file_path):
            print(
                f"Warning: Converted file {converted_filename} not found. Skipping detailed plot."
            )
            continue

        try:
            # Read the CSV file
            df = pd.read_csv(file_path)

            # Convert datetime strings to datetime objects
            df["Date_Of_Measurement(datetime)"] = pd.to_datetime(
                df["Date_Of_Measurement(datetime)"], format="%Y.%m.%d %H:%M:%S"
            )

            # Convert CO2 values to numeric
            df["CO2(ppm)"] = pd.to_numeric(df["CO2(ppm)"])

            # Get start time and duration from config
            start_time_str = plot_config["from"]  # Format: "HH:MM:SS"
            duration_str = plot_config["length"]  # Format: "HH:MM"

            # Get the measurement date
            measurement_date = df["Date_Of_Measurement(datetime)"].iloc[0].date()

            # Create start datetime by combining measurement date with specified time
            start_time = datetime.datetime.strptime(start_time_str, "%H:%M:%S").time()
            start_datetime = datetime.datetime.combine(measurement_date, start_time)

            # Calculate end datetime
            duration = parse_time_duration(duration_str)
            end_datetime = start_datetime + duration

            # Filter data for the specified time range
            mask = (df["Date_Of_Measurement(datetime)"] >= start_datetime) & (
                df["Date_Of_Measurement(datetime)"] <= end_datetime
            )
            filtered_df = df[mask]

            if filtered_df.empty:
                print(
                    f"Warning: No data found in specified time range for {csv_filename}"
                )
                continue

            # Create the detailed plot
            plt.figure(figsize=(12, 8))

            plt.plot(
                filtered_df["Date_Of_Measurement(datetime)"],
                filtered_df["CO2(ppm)"],
                marker="o",
                markersize=3,
                linewidth=1.5,
                color="red",
            )

            # Format x-axis to show time
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))

            # Clean filename for title
            file_title = csv_filename.replace(".csv", "")

            plt.xlabel(f"Time - {measurement_date.strftime('%Y.%m.%d')}")
            plt.ylabel("CO2 (ppm)")
            plt.title(
                f"Detailed CO2 Levels - {file_title} ({start_time_str} - {duration_str})"
            )
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save the detailed plot with unique filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_filename = f"detailed_co2_plot_{file_title}_{start_time_str.replace(':', '')}_{timestamp}.png"
            plot_path = os.path.join(detailed_plots_folder, plot_filename)
            plt.savefig(plot_path, dpi=300, bbox_inches="tight")
            print(f"Detailed plot saved to: {plot_path}")

            plt.close()  # Close the figure to free memory

        except Exception as e:
            print(f"Error creating detailed plot for {csv_filename}: {e}")


def plot_co2_data(
    converted_files_path: str = WRITEPATH,
    save_plot: bool = True,
    plots_folder: str = "plots",
):
    """Plot CO2 levels over time from converted CSV files.
    Creates a separate plot for each CSV file.

    Args:
        converted_files_path (str): Path to directory containing converted CSV files.
        save_plot (bool): Whether to save the plot as an image file.
        plots_folder (str): Folder name to save plots in.
    """
    # Create plots directory if it doesn't exist
    if save_plot and not os.path.exists(plots_folder):
        os.makedirs(plots_folder)

    # Get all converted CSV files
    converted_files = [
        f for f in os.listdir(converted_files_path) if f.endswith(".csv")
    ]

    for csv_file in converted_files:
        file_path = os.path.join(converted_files_path, csv_file)

        # Create a new figure for each file
        plt.figure(figsize=(12, 8))

        # Read the CSV file
        df = pd.read_csv(file_path)

        # Convert datetime strings to datetime objects
        df["Date_Of_Measurement(datetime)"] = pd.to_datetime(
            df["Date_Of_Measurement(datetime)"], format="%Y.%m.%d %H:%M:%S"
        )

        # Convert CO2 values to numeric (in case they're strings)
        df["CO2(ppm)"] = pd.to_numeric(df["CO2(ppm)"])

        # Get the date for the xlabel
        measurement_date = (
            df["Date_Of_Measurement(datetime)"].iloc[0].strftime("%Y.%m.%d")
        )

        # Plot the data using full datetime objects
        plt.plot(
            df["Date_Of_Measurement(datetime)"],
            df["CO2(ppm)"],
            marker="o",
            markersize=3,
            linewidth=1.5,
            color="blue",
        )

        # Format x-axis to show only time
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        # plt.gca().xaxis.set_major_locator(
        #     mdates.MinuteLocator(interval=30)
        # )  # Show labels every 30 minutes

        # Clean filename for title
        file_title = csv_file.replace("converted_", "").replace(".csv", "")

        plt.xlabel(f"Time - {measurement_date}")
        plt.ylabel("CO2 (ppm)")
        plt.title(f"CO2 Levels Over Time - {file_title}")
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot if requested
        if save_plot:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_filename = f"co2_plot_{file_title}_{timestamp}.png"
            plot_path = os.path.join(plots_folder, plot_filename)
            plt.savefig(plot_path, dpi=300, bbox_inches="tight")
            print(f"Plot saved to: {plot_path}")

        plt.close()  # Close the figure to free memory


# Get all CSV files in the specified directory
csv_files = get_csv_files(PATH)

# Process each CSV file
for csv_file in csv_files:
    # Headers for the CSV file
    headers = [
        "CO2(ppm)",
        "Temperature(C)",
        "Maximum_CO2(ppm)",
        "Minimum_CO2(ppm)",
        "Date_Of_Measurement(datetime)",
    ]

    print(f"Processing file: {csv_file}")

    # Get the first line info
    title, date = get_first_line_info(os.path.join(PATH, csv_file))
    print(f"First line info in {csv_file}: {(title, date)}")

    # Create a writable list from the CSV file
    csv_list = create_writable_list(
        os.path.join(PATH, csv_file),
        headers,
        datetime.datetime.strptime(date, "%Y.%m.%d %H:%M:%S"),
    )
    print(
        f"Got CSV dictionary for {csv_file}: {csv_list[:1]}..."
    )  # Print first entry for brevity

    # Write the CSV list to a new file
    output_file = os.path.join(WRITEPATH, f"converted_{csv_file}")
    with open(output_file, "w", newline="") as wf:
        # Write "title" as the first line as a comment
        # wf.write(f"#{title}\n")
        # Write the headers and data
        writer = csv.DictWriter(wf, fieldnames=headers)
        writer.writeheader()
        writer.writerows(csv_list)

    # Notify the user of completion
    print(f"Converted data written to {output_file}\n\n")

# Call the plotting functions after processing all files
# print("All files processed. Creating and saving plots...")
# plot_co2_data()

print("Creating detailed plots based on configuration...")
plot_detailed_co2_data()
