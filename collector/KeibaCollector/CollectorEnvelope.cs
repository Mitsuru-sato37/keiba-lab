using System.Text.Json;
using System.Text.Json.Serialization;

namespace KeibaCollector;

public sealed record CollectorEnvelope(
    [property: JsonPropertyName("schema_version")] string SchemaVersion,
    [property: JsonPropertyName("batch_id")] string BatchId,
    [property: JsonPropertyName("provider")] string Provider,
    [property: JsonPropertyName("provider_version")] string ProviderVersion,
    [property: JsonPropertyName("collected_at")] string CollectedAt,
    [property: JsonPropertyName("records")] IReadOnlyList<CollectorRecord> Records);

public sealed record CollectorRecord(
    [property: JsonPropertyName("record_id")] string RecordId,
    [property: JsonPropertyName("provider_record_type")] string ProviderRecordType,
    [property: JsonPropertyName("provider_record_key")] string ProviderRecordKey,
    [property: JsonPropertyName("source_timestamp")] string SourceTimestamp,
    [property: JsonPropertyName("received_timestamp")] string ReceivedTimestamp,
    [property: JsonPropertyName("effective_from")] string EffectiveFrom,
    [property: JsonPropertyName("effective_to")] string? EffectiveTo,
    [property: JsonPropertyName("payload")] JsonElement Payload,
    [property: JsonPropertyName("payload_checksum")] string PayloadChecksum);

public static class CollectorContract
{
    public const string SchemaVersion = "jra-van-observation-batch/v1";

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = false,
        WriteIndented = false,
    };

    public static CollectorEnvelope Parse(string json)
    {
        var envelope = JsonSerializer.Deserialize<CollectorEnvelope>(json, JsonOptions)
            ?? throw new InvalidDataException("collector envelope is empty");
        if (envelope.SchemaVersion != SchemaVersion)
        {
            throw new InvalidDataException("unsupported schema_version");
        }
        if (string.IsNullOrWhiteSpace(envelope.BatchId)
            || string.IsNullOrWhiteSpace(envelope.Provider)
            || string.IsNullOrWhiteSpace(envelope.ProviderVersion))
        {
            throw new InvalidDataException("batch metadata is incomplete");
        }

        var recordIds = new HashSet<string>(StringComparer.Ordinal);
        foreach (var record in envelope.Records)
        {
            if (string.IsNullOrWhiteSpace(record.RecordId)
                || !recordIds.Add(record.RecordId)
                || string.IsNullOrWhiteSpace(record.PayloadChecksum))
            {
                throw new InvalidDataException("record identity or checksum is invalid");
            }
        }
        return envelope;
    }

    public static string Serialize(CollectorEnvelope envelope)
    {
        return JsonSerializer.Serialize(envelope, JsonOptions);
    }
}
