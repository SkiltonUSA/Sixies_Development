using System;
using System.IO;
using System.Reflection;

internal static class SparkleHeadless
{
    private const BindingFlags StaticAny =
        BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;

    private static object GetField(Type type, string name) =>
        type.GetField(name, StaticAny).GetValue(null);

    private static void SetField(Type type, string name, object value) =>
        type.GetField(name, StaticAny).SetValue(null, value);

    private static object Invoke(Type type, string name, params object[] args) =>
        type.GetMethod(name, StaticAny).Invoke(null, args);

    public static int Main(string[] args)
    {
        if (args.Length != 2)
        {
            Console.Error.WriteLine("usage: SparkleHeadless Sparkle2.exe script.sls");
            return 2;
        }

        var exePath = Path.GetFullPath(args[0]);
        var scriptPath = Path.GetFullPath(args[1]);
        var assembly = Assembly.LoadFrom(exePath);
        var modDisk = assembly.GetType("Sparkle2.ModDisk", throwOnError: true);

        SetField(modDisk, "DoOnErr", false);
        SetField(modDisk, "CmdLine", true);
        SetField(modDisk, "Script", File.ReadAllText(scriptPath));
        Invoke(modDisk, "SetScriptPath", scriptPath);
        Invoke(modDisk, "ResetArrays");
        Invoke(modDisk, "CalcILTab");

        var track = (int[])GetField(modDisk, "Track");
        track[1] = 0;
        for (var t = 1; t <= 39; t++)
        {
            if (t <= 17)
                track[t + 1] = track[t] + (21 * 256);
            else if (t <= 24)
                track[t + 1] = track[t] + (19 * 256);
            else if (t <= 30)
                track[t + 1] = track[t] + (18 * 256);
            else
                track[t + 1] = track[t] + (17 * 256);
        }

        try
        {
            if ((bool)Invoke(modDisk, "BuildDemoFromScript", true))
                return 0;
        }
        catch (TargetInvocationException ex)
        {
            Console.Error.WriteLine("Sparkle2 threw while building.");
            Console.Error.WriteLine("ErrCode: " + GetField(modDisk, "ErrCode"));
            Console.Error.WriteLine("ScriptEntryType: " + GetField(modDisk, "ScriptEntryType"));
            Console.Error.WriteLine("ScriptEntry: " + GetField(modDisk, "ScriptEntry"));
            Console.Error.WriteLine("ScriptLine: " + GetField(modDisk, "ScriptLine"));
            Console.Error.WriteLine("D64Name: " + GetField(modDisk, "D64Name"));
            Console.Error.WriteLine("Inner: " + ex.InnerException);
            return 1;
        }

        Console.Error.WriteLine("Sparkle2 BuildDemoFromScript returned false.");
        return 1;
    }
}
