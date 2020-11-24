<template>
   <v-expansion-panel v-if="image">
    <v-expansion-panel-header>
      <v-row no-gutters>
        <v-col>
          <span v-if="image.tags.length==0">
            <v-chip color="yellow lighten-2">
              <v-icon left>mdi-alert-circle-outline</v-icon>
              No tags
            </v-chip>
          </span>
          <span>
            <v-chip 
              color="green lighten-1" 
              v-for="tag in image.tags" :key="tag" 
              @click.stop="copyTag(tag)">
                {{tag}}
            </v-chip>
          </span>
        </v-col>
        <v-col class="d-flex align-center">
          <v-btn text icon @click.stop="inspect()">
            <v-icon large>mdi-file-code-outline</v-icon>
            <v-dialog v-model="localState.showDef">
              <v-card>
                <v-card-title class="headline green lighten-2">
                  Singularity Definition
                </v-card-title>
                <v-card-text>
                  <pre class="text--primary">{{localState.meta.deffile}}</pre>
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn color="primary" text @click="localState.showDef = false">
                    What a nice definition file!
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
          </v-btn>
          <v-badge :content="image.downloadCount || '0'" overlap color="blue-grey lighten-1">
            <v-icon large>mdi-download</v-icon>
          </v-badge>
        </v-col>
      </v-row>
    </v-expansion-panel-header> 
    <v-expansion-panel-content>
      <v-row v-for="tag in image.tags" :key="tag">
        <v-col>
          <hsk-text-input :label="'Pull '+tag" :static-value="pullURL(tag)">
            <template v-slot:append v-if="canEdit">
              <v-icon color="error" @click="deleteTag(tag)">mdi-delete-outline</v-icon>
            </template>
          </hsk-text-input>
        </v-col>
      </v-row>
      <v-row v-if="canEdit">
        <v-col class="text-center">
            <v-dialog v-model="localState.showAddTag" max-width="300px">
              <template v-slot:activator="{ on, attrs }">
                <v-btn color="primary" text v-bind="attrs" v-on="on">
                  <v-icon>mdi-tag-plus</v-icon> Add Tag
                </v-btn>
              </template>
              <v-card>
                <v-card-title class="headline">Add Tag</v-card-title>
                <v-card-text>
                  <v-text-field v-model="localState.newTag" label="New Tag" solo required></v-text-field>
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn color="warning accent-1" text @click="closeShowAddTag()">Nej, tack</v-btn>
                  <v-btn color="success darken-1" text @click="addTag()" :disabled="!localState.newTag">Do it!</v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>

        </v-col>
      </v-row>

      <v-row>
        <v-col>
          <hsk-text-input label="Created" :static-value="image.createdAt | moment('YYYY-MM-DD HH:mm:ss')"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input label="Created By" :static-value="image.createdBy"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input 
            label="Description" 
            field="description" 
            :obj="image" 
            action="images/update"
            :readonly="!canEdit"
            @updated="image=$event"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input label="Hash" :static-value="image.hash"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input label="Size" :static-value="image.size | prettyBytes()"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input type="yesno" label="Uploaded" :static-value="image.uploaded"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input label="Downloads" :static-value="image.downloadCount"></hsk-text-input>
        </v-col>
      </v-row>
    </v-expansion-panel-content>
   </v-expansion-panel>
</template>
<script lang="ts">
import { Image, InspectAttributes, User } from '@/store/models';
import { clone as _clone, filter as _filter, concat as _concat } from 'lodash';
import Vue from 'vue';

interface State {
  meta: InspectAttributes;
  showDef: boolean;
  newTag: string;
  showAddTag: boolean;
}

export default Vue.extend({
  name: 'ImageDetails',
  props: {
    image: {
      type: Image,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  data: (): { localState: State } => ({
    localState: {
      meta: {
        deffile: '',
      },
      showDef: false,
      newTag: '',
      showAddTag: false,
    },
  }),
  computed: {
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    canEdit(): boolean {
      return !this.readonly && this.image.canEdit(this.currentUser);
    },
  },
  watch: {
    'localState.showAddTag': function showAddTag(val) {
      if (!val) {
        this.closeShowAddTag();
      }
    },
  },
  methods: {
    pullURL(tag: string): string {
      return `library://${this.image.entityName}/${this.image.collectionName}/${this.image.containerName}:${tag}`
    },
    copyTag(tag: string) {
      this.$copyText(this.pullURL(tag))
        .then(() => this.$store.commit('snackbar/showSuccess', "Copied to clipboard."));
    },
    deleteTag(tag: string) {
      const updateImage = _clone(this.image);
      updateImage.tags = _filter(updateImage.tags, t => t !== tag);
      this.saveTags(updateImage)
        .then(() => this.$store.commit('snackbar/showSuccess', 'Tag removed.'))
    },
    addTag() {
      const updateImage = _clone(this.image);
      updateImage.tags = _concat(updateImage.tags, this.localState.newTag);
      this.saveTags(updateImage)
        .then(() => {
          this.$store.commit('snackbar/showSuccess', 'Tag added');
          this.closeShowAddTag();
        });
    },
    saveTags(updateImage: Image): Promise<any> {
      return this.$store.dispatch('images/updateTags', updateImage)
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    inspect() {
      this.$store.dispatch('images/inspect', this.image)
        .then(response => {
          console.log(response);
          this.localState.meta = response;
          this.localState.showDef = true;
        })
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
    },
    closeShowAddTag() {
      this.localState.showAddTag = false;
      this.$nextTick(() => {
        this.localState.newTag = '';
      });
    }
  }
});
</script>