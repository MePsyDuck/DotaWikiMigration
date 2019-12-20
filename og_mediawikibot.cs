using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Net.Http;
using Newtonsoft.Json;
using System.IO;
using Newtonsoft.Json.Linq;
using WikiClientLibrary;
using WikiClientLibrary.Client;
using WikiClientLibrary.Sites;
using WikiClientLibrary.Pages;
using WikiClientLibrary.Files;

namespace SoundMove
{
    class Program
    {
        private static readonly HttpClient client = new HttpClient();
        static string user, pass;
        static void Main(string[] args)
        {
            if (args.Length < 2)
            {
                Console.WriteLine("Error: No Login Details Provided! (Username + Password)");
                return;
            }
            // save our logon details
            user = args[0];
            pass = args[1];
            client.DefaultRequestHeaders.Add("User-Agent", "SanhardDota2WikiEditingBot/1.0");
            Console.WriteLine("=== ACCESS MEDIAWIKI ===");
            MediaWikiLogin(user, pass).Wait();
        }
        async static Task<String> GetResponse(String request)
        {
            var response = "";
            try
            {
                response = await client.GetStringAsync(request);
            }
            catch (System.Net.Http.HttpRequestException se)
            {
                Console.WriteLine("Bad Response from Server (API Down?)");
                Environment.Exit(1);
            }

            return response;
        }
        async static Task<Stream> GetImageResponse(String request)
        {
            Stream stream = await imageClient.GetStreamAsync(request);
            return stream;
        }
        async static Task MediaWikiLogin(String user, String pass)
        {
            var wikiClient = new WikiClient
            {
                // UA of Client Application. The UA of WikiClientLibrary will
                // be append to the end of this when sending requests.
                ClientUserAgent = "SanhardDota2WikiEditingBot/1.0",
            };
            // Create a MediaWiki Site instance with the URL of API endpoint.
            var site = new WikiSite(wikiClient, "https://dota2.gamepedia.com/api.php");
            // Waits for the WikiSite to initialize
            await site.Initialization;
            Console.WriteLine("API version: {0}", site.SiteInfo.Generator);
            try
            {
                await site.LoginAsync(user, pass);
            }
            catch (OperationFailedException ex)
            {
                Console.WriteLine(ex.ErrorMessage);
            }
            Console.WriteLine("Hello, {0}!", site.AccountInfo.Name);
            Console.WriteLine("You're in the following groups: {0}.", string.Join(",", site.AccountInfo.Groups));
            //open the VPK file structure at sounds/
            System.IO.StreamReader setFile = new System.IO.StreamReader(@"sounds.txt");
            string soundEntry;
            while ((soundEntry = setFile.ReadLine()) != null)
            {
            {
                string[] splitSoundEntry = soundEntry.Split('/');
                string vpkRoot = splitSoundEntry[0];
                string root = splitSoundEntry[1];
                string header = splitSoundEntry[2];
                string fileName = splitSoundEntry[3];
                //Console.WriteLine("VPK Root: " + vpkRoot + ". Root:" + root + ". Header: " + header + ". Sound file:" + fileName);

                var page = new WikiPage(site, "File:" + fileName);
                await page.RefreshAsync(PageQueryOptions.FetchContent
                            | PageQueryOptions.ResolveRedirects);
                string newName = "File:" + root + "_" + header + "_" + fileName;
                if (page.Exists)
                {
                    if (newName.ToLower() != page.Title.Replace(" ", "_").ToLower())
                    {
                        Console.WriteLine("Moving " + fileName + " to " + newName);
                        //Replace Category
                        using (StringReader reader = new StringReader(page.Content))
                        {
                            StringBuilder newPageContentBuilder = new StringBuilder();
                            string line;
                            while ((line = reader.ReadLine()) != null)
                                if (line.Length > 10)
                                {
                                Console.WriteLine("scanning " + line + " " + line.IndexOf("[[Category:"));
                                    if (line.Substring(0, 10) == "[[Category")
                                    {
                                        line = "[[Category:" + vpkRoot + " " + root + " " + header.Replace("_", " ") + "]]";
                                    } else if (line.IndexOf("[[Category:") != -1)
                                    {
                                        int index = line.IndexOf("[[Category:");
                                        string splitLine = line.Substring(0, index);
                                    string oldLine = line;
                                        line = line.Substring(0, index) + "\n" + "[[Category:" + vpkRoot + " " + root + " " + header.Replace("_", " ") + "]]";
                                    Console.WriteLine("replacing " + oldLine + "with " + line);
                                    }
                                }
                                newPageContentBuilder.AppendLine(line);
                            }
                            //Console.WriteLine("Old Page Content:\n" + page.Content);
                            //Console.WriteLine("New Page Content:\n" + newPageContentBuilder.ToString().Trim());
                            page.Content = newPageContentBuilder.ToString().Trim();
                        }
                        
                        await page.UpdateContentAsync("Automated Category replacement (moving files to sound_vo categories)", minor: false, bot: true);
                        System.Threading.CancellationTokenSource source = new System.Threading.CancellationTokenSource();
                        System.Threading.CancellationToken token = source.Token;
                        if (newName.ToLower() != page.Title.Replace(" ", "_").ToLower())
                        {
                            await page.MoveAsync(newName, "Automated move to VPK filepath structure", PageMovingOptions.None, AutoWatchBehavior.None, token);
                        }
                    } else
                    {
                       Console.WriteLine("File already processed: " + newName);
                    }


                } else
                {
                    page.Content = "#REDIRECT [[" + newName + "]]";
                    //await page.UpdateContentAsync("Redirecting old sound pages to new ones", minor: false, bot: true);
                    Console.WriteLine("Page " + "File:" + fileName + " does not exist.");
                }
            }
            Console.WriteLine("All operations completed.");
        }
    }
}