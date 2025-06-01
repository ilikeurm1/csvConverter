# csv converter

## cfg file

The config file should look like this:

```json
{
    "detailed_plots": { // Don't change this
        "Test1.csv": { // The csv file name (in the measurements folder !!! not converted_)
            "from": "10:30:00", // Start timestamp (HH:MM:SS)
            "length": "02:15" // Duration of the plot (HH:MM)
        },
        "Test2.csv": {
            "from": "14:00:00", 
            "length": "01:30"
        },
        "Test3.csv": {
            "from": "09:15:00",
            "length": "03:45"
        }
    }
}
```
