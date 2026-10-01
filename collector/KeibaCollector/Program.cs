namespace KeibaCollector;

internal static class Program
{
    private static async Task<int> Main(string[] args)
    {
        if (args.Contains("--self-check", StringComparer.Ordinal))
        {
            Console.WriteLine(CollectorContract.SchemaVersion);
            return 0;
        }

        var input = await Console.In.ReadToEndAsync();
        try
        {
            var envelope = CollectorContract.Parse(input);
            await Console.Out.WriteAsync(CollectorContract.Serialize(envelope));
            return 0;
        }
        catch (Exception error) when (error is JsonException or InvalidDataException)
        {
            await Console.Error.WriteLineAsync($"collector_import_error: {error.Message}");
            return 2;
        }
    }
}
